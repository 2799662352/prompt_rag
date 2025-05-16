#!/usr/bin/env python3

import os
import argparse
import numpy as np
import plotly.graph_objects as go
import chromadb
from umap import UMAP
import webbrowser
import random
from sklearn.cluster import KMeans


class EmbeddingVisualizer:
    """Visualize embeddings from ChromaDB in 3D space using dimensionality reduction."""
    
    def __init__(
        self,
        db_directory: str,
        collection_name: str,
        max_points: int = 2000,
        random_seed: int = 42,
        n_clusters: int = 10,
        outlier_threshold: float = 3.0
    ):
        """Initialize the visualizer with database path and visualization parameters.
        
        Args:
            db_directory: Path to the ChromaDB database directory
            collection_name: Name of the collection in ChromaDB
            output_file: Path where the HTML visualization will be saved
            max_points: Maximum number of points to visualize (for performance)
            random_seed: Random seed for reproducibility
            n_clusters: Number of clusters to create for coloring points
            outlier_threshold: Z-score threshold for outlier removal (higher = more outliers kept)
        """
        self.db_directory = db_directory
        self.collection_name = collection_name
        # Update output directory to artifacts/visualizations
        visualization_dir = "artifacts/visualizations"
        self.output_file = f"{visualization_dir}/visualization_{collection_name}_{random_seed}_{max_points}_{n_clusters}_{outlier_threshold}.html"
        self.max_points = max_points
        self.random_seed = random_seed
        self.n_clusters = n_clusters
        self.outlier_threshold = outlier_threshold
        
        # Set random seed for reproducibility
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
        
        # Initialize the ChromaDB client
        print(f"Connecting to ChromaDB at {db_directory}")
        self.client = chromadb.PersistentClient(path=db_directory)
        
        # Get the collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Found collection: {collection_name} with {self.collection.count()} documents")
        except Exception as e:
            print(f"Error accessing collection: {e}")
            raise
        
    def get_embeddings(self):
        """Retrieve embeddings and metadata from ChromaDB."""
        print("Retrieving embeddings from ChromaDB...")
        
        # Get all embeddings
        result = self.collection.get(
            include=['embeddings', 'documents', 'metadatas']
        )
        
        embeddings = np.array(result['embeddings'])
        documents = result['documents']
        metadatas = result['metadatas']
        ids = result['ids']
        
        print(f"Retrieved {len(embeddings)} embeddings with {embeddings.shape[1]} dimensions")
        
        # If there are too many embeddings, sample a subset
        if len(embeddings) > self.max_points:
            print(f"Sampling {self.max_points} out of {len(embeddings)} points for visualization")
            indices = np.random.choice(len(embeddings), self.max_points, replace=False)
            embeddings = embeddings[indices]
            documents = [documents[i] for i in indices]
            metadatas = [metadatas[i] for i in indices]
            ids = [ids[i] for i in indices]
            
        return embeddings, documents, metadatas, ids
    
    def reduce_dimensions(self, embeddings):
        """Reduce embedding dimensions to 2D and 3D using UMAP."""
        print("Reducing dimensions using UMAP...")
        
        # Reduce to 3D
        reducer_3d = UMAP(n_components=3, random_state=self.random_seed, n_neighbors=15, min_dist=0.1)
        embeddings_3d = reducer_3d.fit_transform(embeddings)
        print(f"Reduced dimensions from {embeddings.shape[1]} to 3")
        
        # Reduce to 2D
        reducer_2d = UMAP(n_components=2, random_state=self.random_seed, n_neighbors=15, min_dist=0.1)
        embeddings_2d = reducer_2d.fit_transform(embeddings)
        print(f"Reduced dimensions from {embeddings.shape[1]} to 2")
        
        return embeddings_2d, embeddings_3d
    
    def cluster_embeddings(self, embeddings):
        """Cluster embeddings for coloring in visualization."""
        print(f"Clustering embeddings into {self.n_clusters} groups...")
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_seed)
        clusters = kmeans.fit_predict(embeddings)
        return clusters
    
    def filter_outliers(self, embeddings_2d, embeddings_3d, documents, metadatas, ids, clusters):
        """Filter out outlier points that are too far from the main clusters.
        
        Uses z-score to identify points that are too far from the center in both 2D and 3D spaces.
        Returns filtered versions of all inputs.
        """
        print(f"Filtering outliers with threshold {self.outlier_threshold}...")
        
        # Calculate z-scores for 3D embeddings along each axis
        z_scores_3d = np.zeros_like(embeddings_3d)
        for dim in range(3):
            mean = np.mean(embeddings_3d[:, dim])
            std = np.std(embeddings_3d[:, dim])
            if std > 0:  # Avoid division by zero
                z_scores_3d[:, dim] = np.abs((embeddings_3d[:, dim] - mean) / std)
        
        # A point is an outlier if its z-score exceeds the threshold in any dimension
        max_z_scores_3d = np.max(z_scores_3d, axis=1)
        outliers_3d = max_z_scores_3d > self.outlier_threshold
        
        # Calculate z-scores for 2D embeddings along each axis
        z_scores_2d = np.zeros_like(embeddings_2d)
        for dim in range(2):
            mean = np.mean(embeddings_2d[:, dim])
            std = np.std(embeddings_2d[:, dim])
            if std > 0:  # Avoid division by zero
                z_scores_2d[:, dim] = np.abs((embeddings_2d[:, dim] - mean) / std)
        
        # A point is an outlier if its z-score exceeds the threshold in any dimension
        max_z_scores_2d = np.max(z_scores_2d, axis=1)
        outliers_2d = max_z_scores_2d > self.outlier_threshold
        
        # Combine both outlier detection methods (a point is kept only if it's not an outlier in either 2D or 3D)
        outliers = outliers_2d | outliers_3d
        
        # Count outliers
        num_outliers = np.sum(outliers)
        print(f"Filtered out {num_outliers} outliers ({num_outliers/len(outliers)*100:.1f}% of points)")
        
        # Keep only non-outlier points
        keep_indices = ~outliers
        embeddings_2d_filtered = embeddings_2d[keep_indices]
        embeddings_3d_filtered = embeddings_3d[keep_indices]
        documents_filtered = [doc for i, doc in enumerate(documents) if keep_indices[i]]
        metadatas_filtered = [meta for i, meta in enumerate(metadatas) if keep_indices[i]]
        ids_filtered = [id for i, id in enumerate(ids) if keep_indices[i]]
        clusters_filtered = clusters[keep_indices]
        
        return embeddings_2d_filtered, embeddings_3d_filtered, documents_filtered, metadatas_filtered, ids_filtered, clusters_filtered
    
    def create_visualization(self, embeddings_2d, embeddings_3d, documents, metadatas, ids, clusters, original_dims):
        """Create an interactive visualization with 2D/3D toggle using Plotly."""
        print("Creating visualization with 2D/3D toggle...")
        
        # Create a color palette
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
            '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
        ]
        
        # Create hover texts
        hover_texts = []
        for i in range(len(documents)):
            # Extract filename from source path
            source_path = metadatas[i]['source']
            filename = os.path.basename(source_path)
            
            # Truncate document text for hover
            doc_preview = documents[i][:200] + "..." if len(documents[i]) > 200 else documents[i]
            doc_preview = doc_preview.replace("\n", "<br>")
            
            hover_text = f"<b>ID:</b> {ids[i]}<br><b>File:</b> {filename}<br><b>Preview:</b><br>{doc_preview}"
            hover_texts.append(hover_text)
        
        # Create the figure with subplots
        fig = go.Figure()
        
        # Add 3D traces (initially visible)
        for cluster_id in range(self.n_clusters):
            cluster_indices = np.where(clusters == cluster_id)[0]
            
            fig.add_trace(go.Scatter3d(
                x=embeddings_3d[cluster_indices, 0],
                y=embeddings_3d[cluster_indices, 1],
                z=embeddings_3d[cluster_indices, 2],
                mode='markers',
                marker=dict(
                    size=5,
                    color=colors[cluster_id % len(colors)],
                    opacity=0.7,
                ),
                text=[hover_texts[i] for i in cluster_indices],
                hoverinfo='text',
                name=f'Cluster {cluster_id}',
                scene='scene',
                visible=True
            ))
        
        # Add 2D traces (initially hidden)
        for cluster_id in range(self.n_clusters):
            cluster_indices = np.where(clusters == cluster_id)[0]
            
            fig.add_trace(go.Scatter(
                x=embeddings_2d[cluster_indices, 0],
                y=embeddings_2d[cluster_indices, 1],
                mode='markers',
                marker=dict(
                    size=8,
                    color=colors[cluster_id % len(colors)],
                    opacity=0.7,
                ),
                text=[hover_texts[i] for i in cluster_indices],
                hoverinfo='text',
                name=f'Cluster {cluster_id}',
                visible=False
            ))
        
        # Create buttons for 2D/3D toggle
        button_3d = dict(
            label="3D View",
            method="update",
            args=[
                {"visible": [True] * self.n_clusters + [False] * self.n_clusters},
                {"scene": {"xaxis": {"title": "UMAP Dimension 1"},
                           "yaxis": {"title": "UMAP Dimension 2"},
                           "zaxis": {"title": "UMAP Dimension 3"}},
                 "xaxis": {"title": ""},
                 "yaxis": {"title": ""},
                 "title": {"text": f"3D Visualization of {self.collection_name} Embeddings (Original Dimensions: {original_dims})",
                           "y": 0.95,
                           "x": 0.5,
                           "xanchor": "center",
                           "yanchor": "top",
                           "font": {"size": 24}}}
            ]
        )
        
        button_2d = dict(
            label="2D View",
            method="update",
            args=[
                {"visible": [False] * self.n_clusters + [True] * self.n_clusters},
                {"xaxis": {"title": "UMAP Dimension 1"},
                 "yaxis": {"title": "UMAP Dimension 2"},
                 "scene": {"xaxis": {"title": ""},
                           "yaxis": {"title": ""},
                           "zaxis": {"title": ""}},
                 "title": {"text": f"2D Visualization of {self.collection_name} Embeddings (Original Dimensions: {original_dims})",
                           "y": 0.95,
                           "x": 0.5,
                           "xanchor": "center",
                           "yanchor": "top",
                           "font": {"size": 24}}}
            ]
        )
        
        # Add dropdown menu
        fig.update_layout(
            updatemenus=[dict(
                type="buttons",
                direction="right",
                x=0.1,  # Move buttons to the left side
                y=1.1,  # Keep at the same height
                showactive=True,
                buttons=[button_3d, button_2d]
            )]
        )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"3D Visualization of {self.collection_name} Embeddings (Original Dimensions: {original_dims})",
                y=0.95,  # Position slightly higher
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(size=24)
            ),
            scene=dict(
                xaxis_title='UMAP Dimension 1',
                yaxis_title='UMAP Dimension 2',
                zaxis_title='UMAP Dimension 3'
            ),
            xaxis_title='',
            yaxis_title='',
            legend=dict(
                x=0.85,  # Move legend to the right side
                y=1,
                traceorder="normal",
                font=dict(
                    family="sans-serif",
                    size=12,
                    color="black"
                ),
            ),
            margin=dict(l=0, r=0, b=0, t=150),  # Increased top margin to ensure title visibility
            template="plotly_white"
        )
        
        return fig
    
    def save_and_open_visualization(self, fig):
        """Save the visualization to HTML and open it in a web browser."""
        print(f"Saving visualization to {self.output_file}...")
        # Ensure the directory exists and delete the file if it already exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        fig.write_html(self.output_file, auto_open=False)
        
        # Open in browser
        abs_path = os.path.abspath(self.output_file)
        print(f"Opening visualization in web browser: {abs_path}")
        webbrowser.open('file://' + abs_path)
    
    def run(self):
        """Run the full visualization process."""
        # Get embeddings from ChromaDB
        embeddings, documents, metadatas, ids = self.get_embeddings()
        
        # Store original dimensions for title
        original_dims = embeddings.shape[1]
        
        # Reduce dimensions for both 2D and 3D
        embeddings_2d, embeddings_3d = self.reduce_dimensions(embeddings)
        
        # Cluster embeddings for coloring
        clusters = self.cluster_embeddings(embeddings)
        
        # Filter outliers
        embeddings_2d, embeddings_3d, documents, metadatas, ids, clusters = self.filter_outliers(
            embeddings_2d, embeddings_3d, documents, metadatas, ids, clusters
        )
        
        # Create visualization with 2D/3D toggle and dimensions in title
        fig = self.create_visualization(embeddings_2d, embeddings_3d, documents, metadatas, ids, clusters, original_dims)
        
        # Save and open in browser
        self.save_and_open_visualization(fig)
        print("Visualization complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize embeddings from ChromaDB in 2D or 3D space.")
    parser.add_argument("--db", "-d", default="artifacts/vector_stores/chroma_db",
                        help="Directory of the ChromaDB database (default: artifacts/chroma_db)")
    parser.add_argument("--collection", "-c", default="godot_docs",
                        help="Name of the collection in ChromaDB (default: godot_docs)")
    parser.add_argument("--max-points", "-m", type=int, default=2000,
                        help="Maximum number of points to visualize (default: 2000)")
    parser.add_argument("--seed", "-s", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--clusters", "-k", type=int, default=10,
                        help="Number of clusters for coloring (default: 10)")
    parser.add_argument("--outlier-threshold", "-o", type=float, default=3.0,
                        help="Z-score threshold for outlier removal; lower values remove more outliers (default: 3.0)")
    
    args = parser.parse_args()
    
    visualizer = EmbeddingVisualizer(
        db_directory=args.db,
        collection_name=args.collection,
        max_points=args.max_points,
        random_seed=args.seed,
        n_clusters=args.clusters,
        outlier_threshold=args.outlier_threshold
    )
    visualizer.run()
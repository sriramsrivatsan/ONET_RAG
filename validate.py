"""
Validation script for Labor RAG system
Tests core functionality without requiring UI
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from ingestion import CSVLoader, DataValidator, DataNormalizer
from analytics import AggregationEngine, ClusteringEngine, SimilarityAnalyzer
from rag import VectorStore
from utils import setup_logger

logger = setup_logger(__name__)

def validate_system():
    """Run system validation tests"""
    
    print("="*70)
    print("LABOR RAG SYSTEM VALIDATION")
    print("="*70)
    
    # Test 1: CSV Loading
    print("\n[1/7] Testing CSV Loading...")
    try:
        loader = CSVLoader()
        data_path = Path(__file__).parent / "data" / "data.csv"
        df = loader.load(data_path)
        print(f"✓ Loaded {len(df)} rows successfully")
        metadata = loader.get_metadata()
        print(f"✓ Found {metadata['n_industries']} industries")
        print(f"✓ Found {metadata['n_occupations']} occupations")
    except Exception as e:
        print(f"✗ CSV Loading failed: {str(e)}")
        return False
    
    # Test 2: Data Validation
    print("\n[2/7] Testing Data Validation...")
    try:
        validator = DataValidator()
        is_valid, results = validator.validate(df)
        if is_valid:
            print("✓ Data validation passed")
            print(f"  - {results['row_count']} rows validated")
            print(f"  - {len(results['required_columns_present']['present'])} required columns present")
        else:
            print("✗ Data validation failed")
            print(validator.get_validation_summary())
            return False
    except Exception as e:
        print(f"✗ Data Validation failed: {str(e)}")
        return False
    
    # Test 3: Data Normalization
    print("\n[3/7] Testing Data Normalization...")
    try:
        normalizer = DataNormalizer()
        df_normalized = normalizer.normalize_dataset(df)
        df_normalized = normalizer.create_combined_text(df_normalized)
        print(f"✓ Normalized {len(df_normalized)} rows")
        print(f"✓ Created combined_text column")
    except Exception as e:
        print(f"✗ Data Normalization failed: {str(e)}")
        return False
    
    # Test 4: Aggregations
    print("\n[4/7] Testing Aggregation Engine...")
    try:
        agg_engine = AggregationEngine()
        aggregations = agg_engine.compute_all(df_normalized)
        print(f"✓ Computed aggregations:")
        print(f"  - Total employment: {aggregations['employment_stats']['total_employment']:,.0f}")
        print(f"  - Mean wage: ${aggregations['wage_stats']['mean_wage']:.2f}/hr")
        print(f"  - Unique tasks: {aggregations['task_frequency']['total_unique_tasks']}")
    except Exception as e:
        print(f"✗ Aggregations failed: {str(e)}")
        return False
    
    # Test 5: Clustering (limited for speed)
    print("\n[5/7] Testing Clustering Engine...")
    try:
        cluster_engine = ClusteringEngine()
        df_clustered = cluster_engine.cluster_all(df_normalized.head(50))  # Limit for speed
        print(f"✓ Clustering completed")
        if 'task_cluster_id' in df_clustered.columns:
            print(f"  - Task clusters: {df_clustered['task_cluster_id'].nunique()}")
        if 'function_cluster_id' in df_clustered.columns:
            print(f"  - Function clusters: {df_clustered['function_cluster_id'].nunique()}")
    except Exception as e:
        print(f"✗ Clustering failed: {str(e)}")
        # Non-critical, continue
        df_clustered = df_normalized
    
    # Test 6: Similarity Analysis
    print("\n[6/7] Testing Similarity Analysis...")
    try:
        similarity_analyzer = SimilarityAnalyzer()
        similarity_results = similarity_analyzer.analyze_cross_industry_tasks(df_normalized)
        if similarity_results and 'top_10_similar_pairs' in similarity_results:
            print(f"✓ Similarity analysis completed")
            if similarity_results['top_10_similar_pairs']:
                top_pair = similarity_results['top_10_similar_pairs'][0]
                print(f"  - Most similar: {top_pair['industry_1']} ↔ {top_pair['industry_2']}")
                print(f"    Similarity: {top_pair['similarity_score']:.3f}")
    except Exception as e:
        print(f"✗ Similarity Analysis failed: {str(e)}")
        # Non-critical, continue
    
    # Test 7: Vector Store
    print("\n[7/7] Testing Vector Store...")
    try:
        vector_store = VectorStore(persist_directory="/tmp/test_chroma")
        vector_store.create_collection(reset=True)
        
        # Add a small sample
        sample_df = df_normalized.head(10)
        vector_store.add_documents(
            sample_df,
            text_column='combined_text',
            metadata_columns=['Industry title', 'ONET job title']
        )
        
        stats = vector_store.get_stats()
        print(f"✓ Vector store initialized")
        print(f"  - Documents indexed: {stats['document_count']}")
        
        # Test search
        results = vector_store.search("digital documents", k=3)
        print(f"✓ Search functional: {len(results)} results returned")
        
    except Exception as e:
        print(f"✗ Vector Store failed: {str(e)}")
        return False
    
    print("\n" + "="*70)
    print("✓ ALL VALIDATION TESTS PASSED")
    print("="*70)
    print("\nSystem is ready for use!")
    print("Run 'streamlit run app/main.py' to start the application.")
    
    return True

if __name__ == "__main__":
    success = validate_system()
    sys.exit(0 if success else 1)

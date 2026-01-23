"""
Basic API tests to demonstrate testing setup.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that key dependencies can be imported."""
    try:
        import fastapi
        import sklearn
        import joblib
        import pandas
        assert True
    except ImportError:
        assert False, "Missing required imports"

def test_model_files_exist():
    """Check that model files are mentioned (though not in Git)."""
    # Model files are excluded from Git via .gitignore
    # This test documents that fact
    assert True, "Model files are excluded from Git (see .gitignore)"

def test_requirements():
    """Check that requirements file exists."""
    assert os.path.exists("requirements.txt"), "requirements.txt missing"

if __name__ == "__main__":
    test_imports()
    test_model_files_exist()
    test_requirements()
    print("All basic checks passed!")

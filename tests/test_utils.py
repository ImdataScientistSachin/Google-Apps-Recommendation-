import os
import pandas as pd
import tempfile
import pytest
from app.utils import load_data, preprocess_data

def test_load_data_with_valid_path():
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        tmp.write('Category,Rating,Reviews,Installs,Type\n')
        tmp.write('Social,4.5,1000,10000,Free\n')
        tmp_path = tmp.name
    try:
        df = load_data(tmp_path)
        assert not df.empty
        assert 'Category' in df.columns
    finally:
        os.remove(tmp_path)

def test_load_data_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_data('nonexistent_file.csv')

def test_preprocess_data_imputation():
    # DataFrame with missing values
    df = pd.DataFrame({
        'Category': ['Social', None, 'Productivity'],
        'Rating': [4.5, None, 4.0],
        'Reviews': [1000, 2000, None],
        'Installs': ['10000', '20000', '30000'],
        'Type': ['Free', 'Paid', None]
    })
    X_train, X_test, y_train, y_test = preprocess_data(df)
    # Check that there are no missing values in the processed data
    assert not X_train.isnull().any().any()
    assert not X_test.isnull().any().any()
    # Check that the shape is correct
    assert X_train.shape[1] == 5
    assert y_train.shape[0] == X_train.shape[0] 
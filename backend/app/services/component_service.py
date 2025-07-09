import pandas as pd
import io
from typing import Dict, Any, List, Tuple

def extract_csv_from_text(text: str) -> str | None:
    """
    Extracts CSV content from a markdown-like text block.
    Looks for blocks starting with ```csv and ending with ```.
    """
    try:
        start_marker = '```csv'
        end_marker = '```'
        
        start_index = text.find(start_marker)
        if start_index == -1:
            return None
            
        end_index = text.find(end_marker, start_index + len(start_marker))
        if end_index == -1:
            return None
            
        csv_content = text[start_index + len(start_marker):end_index].strip()
        return csv_content
    except Exception:
        return None

def analyze_bom_data(bom_text: str) -> Tuple[str, pd.DataFrame]:
    """
    Analyzes the BOM text, extracts CSV data, and returns a status message
    and a pandas DataFrame.
    """
    csv_content = extract_csv_from_text(bom_text)
    if csv_content is None:
        error_msg = "No CSV data found in the provided BOM text."
        empty_df = pd.DataFrame(columns=["器件名称", "单价", "数量", "总价"])
        return error_msg, empty_df

    try:
        bom_data = pd.read_csv(io.StringIO(csv_content))
        
        # Ensure required columns exist
        if '元器件型号' not in bom_data.columns or '数量' not in bom_data.columns:
            raise ValueError("CSV must contain '元器件型号' and '数量' columns.")

        # Add price columns for calculation, initializing to 0
        if 'price' not in bom_data.columns:
            bom_data['price'] = 0
        
        bom_data['总价'] = bom_data['price'] * bom_data['数量']
        
        # Prepare the DataFrame for display
        display_df = bom_data[['元器件型号', 'price', '数量', '总价']].copy()
        display_df.rename(columns={
            '元器件型号': '器件名称',
            'price': '单价'
        }, inplace=True)

        return "BOM data analyzed successfully.", display_df

    except Exception as e:
        error_msg = f"Failed to parse CSV data: {str(e)}"
        empty_df = pd.DataFrame(columns=["器件名称", "单价", "数量", "总价"])
        return error_msg, empty_df

def search_components_in_store(df: pd.DataFrame, store_name: str) -> pd.DataFrame:
    """
    Simulates searching for components in a specific store.
    In this prototype, it applies a discount for a specific store.
    """
    if df.empty:
        return df

    df_copy = df.copy()
    
    # Apply a 10% discount for the specified store as in the notebook
    if store_name == "华秋商城":
        df_copy['单价'] = df_copy['单价'] * 0.9
    
    # Recalculate total price
    df_copy['总价'] = df_copy['单价'] * df_copy['数量']
    
    return df_copy

def calculate_total_price(df: pd.DataFrame) -> float:
    """
    Calculates the total price from the DataFrame.
    """
    if df.empty:
        return 0.0
        
    return df['总价'].sum()

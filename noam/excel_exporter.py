import pandas as pd
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from typing import List, Dict, Any, Optional
import os
from dataclasses import dataclass


@dataclass
class ExcelExportConfig:
    """Configuration for Excel export operations"""
    template_path: str
    output_directory: str
    starting_row: int = 23
    columns_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        if self.columns_mapping is None:
            self.columns_mapping = {
                'A': 'row_number',
                'B': 'part_number', 
                'C': 'description',
                'D': 'quantity',
                'E': 'unit_price',
                'F': 'total_price',
                'G': 'supplier',
                'H': 'notes'
            }


class ExcelTemplateManager:
    """Manages Excel template operations"""
    
    def __init__(self, config: ExcelExportConfig):
        self.config = config
        self._validate_template()
    
    def _validate_template(self):
        """Validate that the template file exists and is accessible"""
        if not os.path.exists(self.config.template_path):
            raise FileNotFoundError(f"Excel template not found: {self.config.template_path}")
    
    def load_template(self) -> Worksheet:
        """Load the Excel template and return the active worksheet"""
        try:
            workbook = load_workbook(self.config.template_path)
            return workbook.active
        except Exception as e:
            raise RuntimeError(f"Failed to load Excel template: {e}")


class DataProcessor:
    """Processes and validates data before Excel export"""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> bool:
        """Validate that the dataframe has the expected structure"""
        if df.empty:
            return False
        
        # Check if dataframe has at least the basic columns
        required_columns = ['name', 'part_number', 'quantity']
        available_columns = df.columns.tolist()
        
        for col in required_columns:
            if col not in available_columns:
                return False
        
        return True
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize the dataframe"""
        # Remove any completely empty rows
        df = df.dropna(how='all')
        
        # Fill NaN values with empty strings
        df = df.fillna('')
        
        # Ensure quantity is numeric
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        
        return df


class ExcelRowMapper:
    """Maps dataframe rows to Excel worksheet rows"""
    
    def __init__(self, config: ExcelExportConfig):
        self.config = config
    
    def map_row_data(self, row_data: List[Any], row_index: int) -> Dict[str, Any]:
        """Map a dataframe row to Excel cell values"""
        row_num = self.config.starting_row + row_index
        
        # Create mapping based on available data
        mapping = {
            'A': row_index + 1,  # Row number
            'B': self._get_value(row_data, 'part_number', 1),  # Part number
            'C': self._create_description(row_data),  # Description
            'D': self._get_value(row_data, 'quantity', 2),  # Quantity
            'E': self._get_value(row_data, 'unit_price', 4),  # Unit price
            'F': self._get_value(row_data, 'total_price', 5),  # Total price
            'G': self._get_value(row_data, 'supplier', 6),  # Supplier
            'H': self._get_value(row_data, 'notes', 7)  # Notes
        }
        
        return {f'{col}{row_num}': value for col, value in mapping.items()}
    
    def _get_value(self, row_data: List[Any], field_name: str, index: int) -> str:
        """Safely get a value from row data"""
        if len(row_data) > index:
            value = row_data[index]
            return str(value) if value is not None else ""
        return ""
    
    def _create_description(self, row_data: List[Any]) -> str:
        """Create a description from name and description fields"""
        name = self._get_value(row_data, 'name', 0)
        description = self._get_value(row_data, 'description', 3)
        
        if description:
            return f"{name}: {description}"
        return name


class ExcelExporter:
    """Main class for exporting data to Excel templates"""
    
    def __init__(self, config: ExcelExportConfig):
        self.config = config
        self.template_manager = ExcelTemplateManager(config)
        self.data_processor = DataProcessor()
        self.row_mapper = ExcelRowMapper(config)
    
    def export_dataframe(self, df: pd.DataFrame, output_filename: str) -> str:
        """
        Export a dataframe to an Excel template
        
        Args:
            df: Pandas DataFrame with the data to export
            output_filename: Name of the output file (without extension)
            
        Returns:
            str: Path to the exported file
        """
        # Validate and clean data
        if not self.data_processor.validate_dataframe(df):
            raise ValueError("Invalid dataframe structure")
        
        df = self.data_processor.clean_dataframe(df)
        
        # Load template
        ws = self.template_manager.load_template()
        
        # Map and write data
        self._write_data_to_worksheet(ws, df)
        
        # Save the file
        output_path = self._save_workbook(ws, output_filename)
        
        return output_path
    
    def _write_data_to_worksheet(self, ws: Worksheet, df: pd.DataFrame):
        """Write dataframe data to the worksheet"""
        for i, row_data in enumerate(df.values):
            cell_mapping = self.row_mapper.map_row_data(row_data, i)
            
            for cell_address, value in cell_mapping.items():
                ws[cell_address] = value
    
    def _save_workbook(self, ws: Worksheet, output_filename: str) -> str:
        """Save the workbook to the output directory"""
        # Ensure output directory exists
        os.makedirs(self.config.output_directory, exist_ok=True)
        
        # Create full output path
        output_path = os.path.join(
            self.config.output_directory, 
            f"{output_filename}.xlsx"
        )
        
        # Save the workbook
        ws.parent.save(output_path)
        
        return output_path


# Factory function for easy creation
def create_excel_exporter(
    template_path: str,
    output_directory: str = "output",
    starting_row: int = 23,
    columns_mapping: Optional[Dict[str, str]] = None
) -> ExcelExporter:
    """
    Factory function to create an ExcelExporter instance
    
    Args:
        template_path: Path to the Excel template file
        output_directory: Directory to save exported files
        starting_row: Starting row for data in the template
        columns_mapping: Custom column mapping (optional)
        
    Returns:
        ExcelExporter: Configured exporter instance
    """
    config = ExcelExportConfig(
        template_path=template_path,
        output_directory=output_directory,
        starting_row=starting_row,
        columns_mapping=columns_mapping
    )
    
    return ExcelExporter(config) 
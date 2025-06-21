#!/usr/bin/env python3
"""Visualize extracted inventory data using matplotlib and torchvision."""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quotient.core.config import QuotientConfig
from quotient.babbage.processors.entity_extractor import EntityExtractor
from quotient.utils.data_models import InventoryItem


def create_inventory_visualization(items, output_path="inventory_visualization.png"):
    """Create a visual representation of inventory data."""
    
    # Set up the figure with a modern style
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    fig.suptitle('Quotient AI - Inventory Data Extraction Results', 
                 fontsize=20, fontweight='bold', y=0.95)
    
    # Filter out items with no meaningful data
    valid_items = [item for item in items if item.quantity > 0 or item.unit_price > 0]
    
    if not valid_items:
        # Create a message if no valid items
        ax1.text(0.5, 0.5, 'No valid inventory items found', 
                ha='center', va='center', transform=ax1.transAxes,
                fontsize=16, style='italic')
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
    else:
        # Create table data
        table_data = []
        for item in valid_items:
            table_data.append([
                item.item_name[:30] + "..." if len(item.item_name) > 30 else item.item_name,
                item.quantity,
                f"${item.unit_price:.2f}",
                f"${item.quantity * item.unit_price:.2f}",
                item.category,
                item.vendor_name[:20] + "..." if len(item.vendor_name) > 20 else item.vendor_name
            ])
        
        # Create table
        table = ax1.table(cellText=table_data,
                         colLabels=['Item Name', 'Quantity', 'Unit Price', 'Total', 'Category', 'Vendor'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.25, 0.1, 0.1, 0.1, 0.15, 0.2])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Color the header
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Color alternating rows
        for i in range(1, len(table_data) + 1):
            for j in range(len(table_data[0])):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        ax1.set_title('Extracted Inventory Items', fontsize=16, fontweight='bold', pad=20)
        ax1.axis('off')
    
    # Create summary statistics
    if valid_items:
        total_items = sum(item.quantity for item in valid_items)
        total_value = sum(item.quantity * item.unit_price for item in valid_items)
        categories = list(set(item.category for item in valid_items if item.category != "Unknown"))
        
        # Summary text
        summary_text = f"""
        📊 EXTRACTION SUMMARY
        
        Total Items: {total_items:,}
        Total Value: ${total_value:.2f}
        Categories Found: {len(categories)}
        Items Extracted: {len(valid_items)}
        
        🏷️ Categories: {', '.join(categories) if categories else 'None identified'}
        """
        
        ax2.text(0.05, 0.9, summary_text, transform=ax2.transAxes,
                fontsize=12, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.7))
        
        # Create a bar chart of quantities
        if len(valid_items) > 1:
            names = [item.item_name[:15] + "..." if len(item.item_name) > 15 else item.item_name 
                    for item in valid_items]
            quantities = [item.quantity for item in valid_items]
            
            bars = ax2.barh(range(len(names)), quantities, 
                           color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'][:len(names)])
            
            # Add value labels on bars
            for i, (bar, qty) in enumerate(zip(bars, quantities)):
                ax2.text(bar.get_width() + max(quantities) * 0.01, bar.get_y() + bar.get_height()/2,
                        str(qty), ha='left', va='center', fontweight='bold')
            
            ax2.set_yticks(range(len(names)))
            ax2.set_yticklabels(names)
            ax2.set_xlabel('Quantity')
            ax2.set_title('Item Quantities', fontsize=14, fontweight='bold')
            ax2.grid(axis='x', alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'Single item extracted', 
                    ha='center', va='center', transform=ax2.transAxes,
                    fontsize=14, style='italic')
            ax2.axis('off')
    else:
        ax2.text(0.5, 0.5, 'No data to visualize', 
                ha='center', va='center', transform=ax2.transAxes,
                fontsize=14, style='italic')
        ax2.axis('off')
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fig.text(0.02, 0.02, f'Generated: {timestamp}', fontsize=8, style='italic')
    
    # Save the visualization
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"✅ Visualization saved as: {output_path}")
    return output_path


def create_modern_dashboard(items, output_path="inventory_dashboard.png"):
    """Create a modern dashboard-style visualization."""
    
    # Set up the figure with a dark theme
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#1a1a1a')
    
    # Create grid layout
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('QUOTIENT AI - INVENTORY EXTRACTION DASHBOARD', 
                 fontsize=24, fontweight='bold', color='white', y=0.95)
    
    # Filter valid items
    valid_items = [item for item in items if item.quantity > 0 or item.unit_price > 0]
    
    if valid_items:
        # 1. Summary metrics (top row)
        total_items = sum(item.quantity for item in valid_items)
        total_value = sum(item.quantity * item.unit_price for item in valid_items)
        avg_price = total_value / total_items if total_items > 0 else 0
        
        # Metric boxes
        metrics = [
            ('Total Items', f'{total_items:,}', '#FF6B6B'),
            ('Total Value', f'${total_value:.2f}', '#4ECDC4'),
            ('Avg Price', f'${avg_price:.2f}', '#45B7D1'),
            ('Items Found', f'{len(valid_items)}', '#96CEB4')
        ]
        
        for i, (label, value, color) in enumerate(metrics):
            ax = fig.add_subplot(gs[0, i])
            ax.text(0.5, 0.6, value, ha='center', va='center', 
                   fontsize=24, fontweight='bold', color=color)
            ax.text(0.5, 0.3, label, ha='center', va='center', 
                   fontsize=12, color='white')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            ax.add_patch(FancyBboxPatch((0.1, 0.1), 0.8, 0.8, 
                                       boxstyle="round,pad=0.02", 
                                       facecolor='#2a2a2a', edgecolor=color, linewidth=2))
        
        # 2. Quantity distribution (middle left)
        ax1 = fig.add_subplot(gs[1, :2])
        names = [item.item_name[:20] + "..." if len(item.item_name) > 20 else item.item_name 
                for item in valid_items]
        quantities = [item.quantity for item in valid_items]
        
        bars = ax1.barh(range(len(names)), quantities, 
                       color=plt.cm.viridis(np.linspace(0, 1, len(names))))
        ax1.set_yticks(range(len(names)))
        ax1.set_yticklabels(names, color='white')
        ax1.set_xlabel('Quantity', color='white')
        ax1.set_title('Item Quantities', color='white', fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # 3. Price distribution (middle right)
        ax2 = fig.add_subplot(gs[1, 2:])
        prices = [item.unit_price for item in valid_items]
        
        ax2.bar(range(len(prices)), prices, 
               color=plt.cm.plasma(np.linspace(0, 1, len(prices))))
        ax2.set_xticks(range(len(prices)))
        ax2.set_xticklabels([f'Item {i+1}' for i in range(len(prices))], rotation=45, color='white')
        ax2.set_ylabel('Unit Price ($)', color='white')
        ax2.set_title('Unit Prices', color='white', fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        # 4. Detailed table (bottom)
        ax3 = fig.add_subplot(gs[2, :])
        table_data = []
        for item in valid_items:
            table_data.append([
                item.item_name[:25] + "..." if len(item.item_name) > 25 else item.item_name,
                item.quantity,
                f"${item.unit_price:.2f}",
                f"${item.quantity * item.unit_price:.2f}",
                item.category,
                item.vendor_name[:15] + "..." if len(item.vendor_name) > 15 else item.vendor_name
            ])
        
        table = ax3.table(cellText=table_data,
                         colLabels=['Item', 'Qty', 'Unit Price', 'Total', 'Category', 'Vendor'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.3, 0.1, 0.1, 0.1, 0.15, 0.2])
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        
        # Style table
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(table_data) + 1):
            for j in range(len(table_data[0])):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#3a3a3a')
                else:
                    table[(i, j)].set_facecolor('#2a2a2a')
                table[(i, j)].set_text_props(color='white')
        
        ax3.set_title('Detailed Inventory Data', color='white', fontweight='bold', pad=20)
        ax3.axis('off')
        
    else:
        # No data message
        ax = fig.add_subplot(gs[:, :])
        ax.text(0.5, 0.5, 'No inventory data to display', 
               ha='center', va='center', transform=ax.transAxes,
               fontsize=20, color='white', style='italic')
        ax.axis('off')
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fig.text(0.02, 0.02, f'Generated: {timestamp}', fontsize=8, style='italic', color='gray')
    
    # Save the dashboard
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#1a1a1a')
    plt.show()
    
    print(f"✅ Dashboard saved as: {output_path}")
    return output_path


def main():
    """Main function to test visualization with extracted data."""
    
    # Test data (same as our previous extraction)
    test_text = """
    Invoice #12345
    
    Qty: 100 pcs - Resistor 10kΩ 1/4W - $0.05 each - Total: $5.00
    Qty: 50 pcs - Capacitor 100µF 25V - $0.10 each - Total: $5.00
    Qty: 25 pcs - LED Red 5mm - $0.02 each - Total: $0.50
    
    Vendor: ABC Electronics Inc.
    Part Numbers: RES-10K-1/4W, CAP-100UF-25V, LED-RED-5MM
    """
    
    print("🔄 Extracting inventory data...")
    
    # Extract data using Babbage
    config = QuotientConfig()
    config.llm_backend = "llama"
    config.llm_id = "microsoft/DialoGPT-medium"
    
    extractor = EntityExtractor(config)
    items = extractor.extract_inventory_items(test_text)
    
    print(f"✅ Extracted {len(items)} inventory items")
    
    # Create visualizations
    print("🎨 Creating visualizations...")
    
    # Standard table visualization
    create_inventory_visualization(items, "inventory_table.png")
    
    # Modern dashboard
    create_modern_dashboard(items, "inventory_dashboard.png")
    
    print("🎉 Visualization complete!")
    print("📁 Files created:")
    print("   - inventory_table.png (Standard table view)")
    print("   - inventory_dashboard.png (Modern dashboard)")


if __name__ == "__main__":
    main() 
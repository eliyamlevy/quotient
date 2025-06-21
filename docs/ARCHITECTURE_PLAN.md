# Quotient Architecture Plan

## Overview
Quotient is an AI-powered inventory management system with a modular, three-layer architecture:

---

## Layer 1: Ingestion & Extraction ("Babbage")
**Purpose:**
- Ingests documents (PDF, images, spreadsheets, etc.)
- Extracts structured inventory data using LLMs and rule-based methods
- Normalizes and cleans extracted data

**Current Status:**
- Multi-format extractors implemented (PDF, image, spreadsheet)
- LLM and rule-based entity extraction working (local and CUDA)
- Data normalization in place

**Next Steps:**
- [ ] Fix CSV extraction bug and improve pandas compatibility
- [ ] Improve LLM prompt and post-processing for more reliable JSON output
- [ ] Enhance OCR and PDF extraction quality
- [ ] Expand rule-based extraction for more item types
- [ ] Add more robust error handling and logging

---

## Layer 2: Analysis & Insights ("Magellan")
**Purpose:**
- Aggregates and analyzes extracted inventory data
- Provides insights, trends, and anomaly detection
- Supports advanced queries and reporting

**Current Status:**
- (Planned) - Not yet implemented

**Next Steps:**
- [ ] Design data models for inventory analytics
- [ ] Implement aggregation and summary statistics
- [ ] Add trend analysis and anomaly detection modules
- [ ] Build API for querying inventory insights
- [ ] Integrate with Layer 1 (Babbage) output

---

## Layer 3: Interface & Integration ("Hopper")
**Purpose:**
- User-facing web dashboard and/or API
- Visualization of inventory, trends, and analytics
- Integration with external systems (ERP, procurement, etc.)

**Current Status:**
- (Planned) - Not yet implemented
- Visualization script (matplotlib) available for Layer 1 output

**Next Steps:**
- [ ] Design and prototype web dashboard (e.g., with FastAPI + React or Streamlit)
- [ ] Build REST API for inventory data and analytics
- [ ] Add authentication and user management
- [ ] Integrate with external systems (optional)
- [ ] Enhance visualization with interactive charts and filtering

---

## General Roadmap
- [ ] Complete Layer 1 (Babbage) stabilization and bug fixes
- [ ] Begin Layer 2 (Magellan) analytics and data modeling
- [ ] Prototype Layer 3 (Hopper) dashboard and API
- [ ] Gather user feedback and iterate

---

**Last updated:** June 2025 
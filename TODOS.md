# TODOS for Quotient (Slim Branch)

## 1. CSV Extraction Bug
- [ ] Fix the error in the CSV extractor: `read_csv() got an unexpected keyword argument 'errors'`
- [ ] Ensure compatibility with the installed pandas version
- [ ] Add a test for CSV extraction

## 2. LLM Output Format
- [ ] Improve the prompt for the LLM to reliably return a valid JSON array
- [ ] Add post-processing to extract JSON from less structured LLM output
- [ ] Consider using a smaller or more instruction-tuned model for better extraction

## 3. PDF Extraction Quality
- [ ] Investigate and improve OCR/text extraction for PDFs (garbled item names)
- [ ] Tune OCR parameters or try higher-quality sample PDFs
- [ ] Add more robust error handling for PDF extraction

## 4. Visualization Unicode Warnings
- [ ] Optionally install a font that supports all Unicode glyphs for matplotlib
- [ ] Replace or remove unsupported emoji/icons in the visualization if needed

## 5. General Improvements
- [ ] Add more real-world sample data for testing
- [ ] Expand rule-based extraction for more item types
- [ ] Add more tests for edge cases and error handling

---

**Last updated:** $(date) 
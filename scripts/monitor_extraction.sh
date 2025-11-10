#!/bin/bash
# Monitor extraction progress

echo "========================================"
echo "  EXTRACTION PROGRESS MONITOR"
echo "========================================"
echo ""

# Check if extraction is running
if pgrep -f "extract_voters_universal.py" > /dev/null; then
    echo "✅ Extraction is RUNNING"
    echo ""
    
    # Show latest progress from log
    echo "Latest progress:"
    echo "----------------"
    tail -n 10 /tmp/kolkata_south_extraction.log | grep -E "Extracting|Processing|COMPLETE"
    
    echo ""
    echo "Full log: /tmp/kolkata_south_extraction.log"
    echo "Monitor live: tail -f /tmp/kolkata_south_extraction.log"
else
    echo "⏸️  Extraction is NOT running"
    echo ""
    echo "Check log for completion status:"
    tail -n 20 /tmp/kolkata_south_extraction.log
fi

echo ""
echo "========================================"

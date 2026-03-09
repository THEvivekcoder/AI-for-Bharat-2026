// Node.js script to convert CSV to JSON
const fs = require('fs');
const path = require('path');

function parseCSV(csvText) {
  const lines = csvText.split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  const schemes = [];
  
  let currentLine = '';
  let inQuotes = false;
  
  for (let i = 1; i < lines.length; i++) {
    currentLine += lines[i];
    
    // Count quotes to determine if we're inside a quoted field
    const quoteCount = (currentLine.match(/"/g) || []).length;
    inQuotes = quoteCount % 2 !== 0;
    
    if (!inQuotes && currentLine.trim()) {
      const values = parseCSVLine(currentLine);
      
      if (values.length >= 8) {
        const scheme = {
          id: values[1] || `scheme-${i}`,
          name: cleanText(values[0]),
          slug: values[1],
          details: cleanText(values[2]),
          benefits: cleanText(values[3]),
          eligibility: cleanText(values[4]),
          application: cleanText(values[5]),
          documents: cleanText(values[6]),
          level: values[7],
          category: values[8] || 'General',
          tags: values[10] || ''
        };
        
        schemes.push(scheme);
      }
      
      currentLine = '';
    } else if (!inQuotes) {
      currentLine = '';
    }
  }
  
  return schemes;
}

function parseCSVLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  
  values.push(current.trim());
  return values;
}

function cleanText(text) {
  return text
    .replace(/^["']+|["']+$/g, '')
    .replace(/""/g, '"')
    .trim();
}

// Read CSV
const csvPath = path.join(__dirname, '../../data/updated_data.csv');
const csvText = fs.readFileSync(csvPath, 'utf-8');

// Parse CSV
const schemes = parseCSV(csvText);

// Write JSON
const outputPath = path.join(__dirname, 'schemes-data.js');
const jsContent = `// Auto-generated from CSV dataset
const schemesData = ${JSON.stringify(schemes, null, 2)};

// Export for use in browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = schemesData;
}
`;

fs.writeFileSync(outputPath, jsContent);
console.log(`Converted ${schemes.length} schemes to schemes-data.js`);

"""Google Sheets tools for searching and reading data with intelligent relevance scoring"""

from langchain_core.tools import tool
from typing import Optional
import sys
import os

# Add parent directory to path to import google_sheets_auth
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from google_sheets_auth import GoogleSheetsAuth
    sheets_auth = GoogleSheetsAuth()
    SHEETS_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Google Sheets tools unavailable: {e}")
    sheets_auth = None
    SHEETS_AVAILABLE = False


@tool
def find_in_google_sheet(
    spreadsheet_id: str,
    keywords: str,
    sheet_name: Optional[str] = None
) -> str:
    """Search for keywords in a Google Sheet and return ONLY the most relevant matching rows.
    
    This tool intelligently matches keywords to find content related to your topic.
    It prioritizes rows where:
    - Multiple keywords appear together
    - Keywords appear in titles/headers (first column)
    - Keywords appear close to each other
    
    Args:
        spreadsheet_id: The Google Sheets ID (from URL)
        keywords: Keywords to search for (space-separated, e.g., 'intake management procurement')
        sheet_name: Optional specific sheet/tab name to search in
    
    Returns:
        String with the MOST RELEVANT matching rows (not all matches, only best ones)
    
    Examples:
        find_in_google_sheet("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms", "intake management")
    """
    print(f"\n{'🔍'*30}")
    print(f"[GOOGLE SHEETS TOOL CALLED] find_in_google_sheet")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"Keywords: {keywords}")
    print(f"Sheet Name: {sheet_name or 'All sheets'}")
    print(f"{'🔍'*30}\n")
    
    if not SHEETS_AVAILABLE or not sheets_auth:
        return "Error: Google Sheets authentication not configured. Please set up OAuth first."
    
    if not sheets_auth.is_authenticated():
        return "Error: Not authenticated with Google Sheets. Please complete OAuth flow first."
    
    try:
        service = sheets_auth.get_service()
        
        # Get sheet data
        range_name = f"{sheet_name}!A1:ZZ" if sheet_name else "A1:ZZ"
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return "No data found in the specified sheet"
        
        # Parse keywords
        keyword_list = [k.strip().lower() for k in keywords.split() if k.strip()]
        if not keyword_list:
            return "Error: No valid keywords provided"
        
        headers = values[0] if values else []
        scored_matches = []
        
        # Score each row for relevance
        for i, row in enumerate(values[1:], start=2):
            # Skip empty rows
            if not row or all(not str(cell).strip() for cell in row):
                continue
            
            # Build searchable text from row
            row_text = " ".join(str(cell).lower() for cell in row)
            first_column = str(row[0]).lower() if row else ""
            
            # Calculate relevance score
            score = 0
            matched_keywords = []
            
            # Exact phrase match (highest score)
            full_phrase = " ".join(keyword_list)
            if full_phrase in row_text:
                score += 10
                matched_keywords = keyword_list
            else:
                # Individual keyword matches
                for keyword in keyword_list:
                    if keyword in row_text:
                        matched_keywords.append(keyword)
                        # Higher score if keyword is in first column (usually title/name)
                        if keyword in first_column:
                            score += 5
                        else:
                            score += 2
            
            # Bonus for multiple keywords in same row
            if len(matched_keywords) >= 2:
                score += len(matched_keywords) * 3
            
            # Only include rows with matches
            if score > 0:
                # Build row dict
                row_dict = {}
                for j, header in enumerate(headers):
                    cell_value = row[j] if j < len(row) else ""
                    row_dict[header] = cell_value
                
                row_dict['_row_number'] = i
                row_dict['_relevance_score'] = score
                row_dict['_matched_keywords'] = matched_keywords
                
                scored_matches.append(row_dict)
        
        if not scored_matches:
            return f"No relevant matches found for: {keywords}\n\nTry searching with different or more specific keywords."
        
        # Sort by relevance score (highest first)
        scored_matches.sort(key=lambda x: x['_relevance_score'], reverse=True)
        
        # Return only TOP 10 most relevant results
        top_matches = scored_matches[:10]
        
        # Format results
        result_text = f"Found {len(top_matches)} RELEVANT results for '{keywords}' (out of {len(scored_matches)} total matches):\n\n"
        
        for idx, match in enumerate(top_matches, 1):
            result_text += f"#{idx} (Relevance: {match['_relevance_score']}, Keywords: {', '.join(match['_matched_keywords'])})\n"
            result_text += f"Row {match['_row_number']}:\n"
            
            for key, value in match.items():
                if not key.startswith('_') and value:  # Skip internal fields
                    # Truncate very long values
                    value_str = str(value)
                    if len(value_str) > 200:
                        value_str = value_str[:200] + "..."
                    result_text += f"  {key}: {value_str}\n"
            result_text += "\n"
        
        if len(scored_matches) > 10:
            result_text += f"\n💡 TIP: {len(scored_matches) - 10} more matches available. Try more specific keywords to narrow results.\n"
        
        return result_text
    
    except Exception as e:
        return f"Error searching Google Sheet: {str(e)}\n\nMake sure:\n1. The spreadsheet ID is correct\n2. The sheet is shared with your Google account\n3. You have proper permissions"


@tool
def search_sheet_for_urls(
    spreadsheet_id: str,
    topic_keywords: str,
    sheet_name: Optional[str] = None
) -> str:
    """Search Google Sheet specifically for URLs/links related to a topic.
    
    This tool finds rows that contain BOTH:
    1. A URL/link (http/https)
    2. Content related to your topic keywords
    
    Use this when you need to find reference links, blog posts, or documentation URLs.
    
    Args:
        spreadsheet_id: The Google Sheets ID
        topic_keywords: Topic to search for (e.g., 'intake management procurement')
        sheet_name: Optional specific sheet/tab name
    
    Returns:
        List of URLs with their descriptions, sorted by relevance
    """
    print(f"\n{'🔗'*30}")
    print(f"[GOOGLE SHEETS TOOL CALLED] search_sheet_for_urls")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"Topic Keywords: {topic_keywords}")
    print(f"Sheet Name: {sheet_name or 'All sheets'}")
    print(f"{'🔗'*30}\n")
    
    if not SHEETS_AVAILABLE or not sheets_auth:
        return "Error: Google Sheets authentication not configured."
    
    if not sheets_auth.is_authenticated():
        return "Error: Not authenticated with Google Sheets."
    
    try:
        service = sheets_auth.get_service()
        
        range_name = f"{sheet_name}!A1:ZZ" if sheet_name else "A1:ZZ"
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return "No data found"
        
        keyword_list = [k.strip().lower() for k in topic_keywords.split() if k.strip()]
        headers = values[0] if values else []
        url_matches = []
        
        for i, row in enumerate(values[1:], start=2):
            if not row:
                continue
            
            # Find URLs in this row
            urls_in_row = []
            for cell in row:
                cell_str = str(cell)
                if 'http://' in cell_str or 'https://' in cell_str:
                    urls_in_row.append(cell_str)
            
            if not urls_in_row:
                continue  # Skip rows without URLs
            
            # Check if row is relevant to topic
            row_text = " ".join(str(cell).lower() for cell in row)
            score = 0
            matched_keywords = []
            
            # Check for full phrase match first
            full_phrase = " ".join(keyword_list)
            if full_phrase in row_text:
                score += 10
                matched_keywords = keyword_list
            else:
                # Individual keyword matches
                for keyword in keyword_list:
                    if keyword in row_text:
                        score += 2
                        matched_keywords.append(keyword)
            
            # Bonus for multiple keyword matches
            if len(matched_keywords) >= 2:
                score += len(matched_keywords) * 2
            
            # Only include if relevant (has at least one keyword match)
            if score > 0:
                # Build description from row
                row_dict = {}
                for j, header in enumerate(headers):
                    if j < len(row):
                        row_dict[header] = row[j]
                
                for url in urls_in_row:
                    url_matches.append({
                        'url': url,
                        'description': row_dict,
                        'score': score,
                        'matched_keywords': matched_keywords,
                        'row_number': i
                    })
        
        if not url_matches:
            return f"No URLs found related to: {topic_keywords}\n\nThe sheet may not contain relevant links for this topic."
        
        # Sort by relevance
        url_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top 15 URLs
        top_urls = url_matches[:15]
        
        result_text = f"Found {len(top_urls)} relevant URLs for '{topic_keywords}':\n\n"
        
        for idx, match in enumerate(top_urls, 1):
            result_text += f"{idx}. {match['url']}\n"
            result_text += f"   Keywords matched: {', '.join(match['matched_keywords'])}\n"
            
            # Show title/description if available
            desc = match['description']
            if desc:
                # Try to find a title-like field
                title_field = None
                for key in ['Title', 'Name', 'Page Title', 'Article', 'Link Text', 'Heading']:
                    if key in desc and desc[key]:
                        title_field = desc[key]
                        break
                
                if not title_field and desc:
                    # Use first non-URL field as title
                    for value in desc.values():
                        if value and 'http' not in str(value):
                            title_field = value
                            break
                
                if title_field:
                    result_text += f"   Description: {title_field}\n"
            
            result_text += "\n"
        
        if len(url_matches) > 15:
            result_text += f"... and {len(url_matches) - 15} more URLs\n"
        
        return result_text
    
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def read_google_sheet(
    spreadsheet_id: str,
    sheet_name: Optional[str] = None,
    range_notation: str = "A1:Z100"
) -> str:
    """Read data from a Google Sheet.
    
    Args:
        spreadsheet_id: The Google Sheets ID (from URL)
        sheet_name: Optional specific sheet/tab name
        range_notation: Cell range to read (e.g., 'A1:Z100', 'A:E')
    
    Returns:
        String with sheet data in readable format
    """
    print(f"\n{'📊'*30}")
    print(f"[GOOGLE SHEETS TOOL CALLED] read_google_sheet")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"Sheet Name: {sheet_name or 'Default'}")
    print(f"Range: {range_notation}")
    print(f"{'📊'*30}\n")
    
    if not SHEETS_AVAILABLE or not sheets_auth:
        return "Error: Google Sheets authentication not configured"
    
    if not sheets_auth.is_authenticated():
        return "Error: Not authenticated with Google Sheets"
    
    try:
        service = sheets_auth.get_service()
        
        range_name = f"{sheet_name}!{range_notation}" if sheet_name else range_notation
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return "No data found in the specified range"
        
        # Format as text
        output = f"Data from sheet (showing {len(values)} rows):\n\n"
        headers = values[0] if values else []
        
        for i, row in enumerate(values[:50], 1):  # Limit to 50 rows
            if i == 1:
                output += "Headers: " + " | ".join(str(cell) for cell in row) + "\n"
                output += "-" * 80 + "\n"
            else:
                output += f"Row {i}: " + " | ".join(str(row[j]) if j < len(row) else "" for j in range(len(headers))) + "\n"
        
        if len(values) > 50:
            output += f"\n... and {len(values) - 50} more rows"
        
        return output
    
    except Exception as e:
        return f"Error reading Google Sheet: {str(e)}"


@tool
def list_google_sheets(spreadsheet_id: str) -> str:
    """List all sheets/tabs in a Google Spreadsheet.
    
    Args:
        spreadsheet_id: The Google Sheets ID (from the URL after /d/)
    
    Returns:
        String with list of sheet names
    
    Example:
        list_google_sheets("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
    """
    print(f"\n{'📋'*30}")
    print(f"[GOOGLE SHEETS TOOL CALLED] list_google_sheets")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"{'📋'*30}\n")
    
    if not SHEETS_AVAILABLE or not sheets_auth:
        return "Error: Google Sheets authentication not configured"
    
    if not sheets_auth.is_authenticated():
        return "Error: Not authenticated with Google Sheets"
    
    try:
        service = sheets_auth.get_service()
        
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        
        if not sheets:
            return "No sheets found in this spreadsheet"
        
        result_text = f"Found {len(sheets)} sheet(s):\n\n"
        for sheet in sheets:
            properties = sheet.get('properties', {})
            title = properties.get('title', 'Untitled')
            sheet_id = properties.get('sheetId', 'N/A')
            row_count = properties.get('gridProperties', {}).get('rowCount', 'N/A')
            col_count = properties.get('gridProperties', {}).get('columnCount', 'N/A')
            
            result_text += f"📄 {title}\n"
            result_text += f"   ID: {sheet_id}\n"
            result_text += f"   Size: {row_count} rows × {col_count} columns\n\n"
        
        return result_text
    
    except Exception as e:
        return f"Error listing sheets: {str(e)}"

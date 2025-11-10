#!/usr/bin/env python3
"""
Quick script to view the Salesforce data that was retrieved
"""
import json
import os
from pathlib import Path

def view_opportunity():
    """View the opportunity record"""
    files = sorted(Path("mcp_output").glob("get_record_*.json"))
    if not files:
        print("No opportunity records found")
        return
    
    latest = files[-1]
    print(f"\n📄 Reading: {latest}")
    print("=" * 80)
    
    with open(latest) as f:
        # The data is stored as a Python tuple string, need to eval it
        content = f.read()
        # Extract the JSON from the tuple
        data = eval(content)[0]
        data = json.loads(data)
    
    # Key fields
    print(f"\n🎯 OPPORTUNITY: {data.get('Name')}")
    print(f"   ID: {data.get('Id')}")
    print(f"   Stage: {data.get('StageName')}")
    print(f"   Amount: ${data.get('Amount'):,.0f}")
    print(f"   Close Date: {data.get('CloseDate')}")
    print(f"   Probability: {data.get('Probability')}%")
    print(f"   Account ID: {data.get('AccountId')}")
    
    print(f"\n📝 Description:")
    print(f"   {data.get('Description') or 'N/A'}")
    
    print(f"\n🔗 Products:")
    products = data.get('Products__c', '').split(';') if data.get('Products__c') else []
    for p in products[:10]:  # First 10
        print(f"   • {p}")
    if len(products) > 10:
        print(f"   ... and {len(products) - 10} more")
    
    print(f"\n📊 Key Metrics:")
    print(f"   Revenue: ${data.get('Revenue__c', 0):,.0f}")
    print(f"   Services Amount: ${data.get('Services_Amount__c', 0):,.0f}")
    print(f"   Deal Score: {data.get('Deal_Score__c')}")
    
    print(f"\n👥 Contacts:")
    print(f"   Owner: {data.get('OwnerId')}")
    print(f"   Contact: {data.get('ContactId')}")
    
    print(f"\n📅 Dates:")
    print(f"   Created: {data.get('CreatedDate')}")
    print(f"   Last Modified: {data.get('LastModifiedDate')}")
    print(f"   Last Activity: {data.get('Last_Activity__c')}")

def view_account_planning_schema():
    """View the Account Planning Document schema"""
    files = sorted(Path("mcp_output").glob("describe_object_*Account*.json"))
    if not files:
        print("\nNo Account Planning Document schema found")
        return
    
    latest = files[-1]
    print(f"\n\n📋 Reading: {latest}")
    print("=" * 80)
    
    with open(latest) as f:
        content = f.read()
        data = eval(content)[0]
        data = json.loads(data)
    
    print(f"\n🏗️  OBJECT: {data.get('name')}")
    print(f"   Label: {data.get('label')}")
    print(f"   API Name: {data.get('name')}")
    
    fields = data.get('fields', [])
    print(f"\n📊 Fields ({len(fields)} total):")
    
    # Show key fields
    key_fields = [f for f in fields if not f.get('name', '').startswith('System')][:20]
    for field in key_fields:
        print(f"   • {field.get('label')} ({field.get('name')})")
        print(f"     Type: {field.get('type')}, Required: {field.get('nillable') == False}")

def main():
    print("\n" + "=" * 80)
    print("🔍 SALESFORCE DATA VIEWER")
    print("=" * 80)
    
    if not os.path.exists("mcp_output"):
        print("\n❌ No mcp_output directory found")
        print("   Run the agent first to retrieve Salesforce data")
        return
    
    view_opportunity()
    view_account_planning_schema()
    
    print("\n" + "=" * 80)
    print("✅ Done! Full data available in mcp_output/ directory")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

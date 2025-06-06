"""Campaign-related functionality for Meta Ads API."""

import json
from typing import List, Optional, Dict, Any, Union
from .api import meta_api_tool, make_api_request
from .accounts import get_ad_accounts
from .server import mcp_server


@mcp_server.tool()
@meta_api_tool
async def get_campaigns(access_token: str = None, account_id: str = None, limit: int = 10, status_filter: str = "", after: str = "") -> str:
    """
    Get campaigns for a Meta Ads account with optional filtering.
    
    Note: By default, the Meta API returns a subset of available fields. 
    Other fields like 'effective_status', 'special_ad_categories', 
    'lifetime_budget', 'spend_cap', 'budget_remaining', 'promoted_object', 
    'source_campaign_id', etc., might be available but require specifying them
    in the API call (currently not exposed by this tool's parameters).
    
    Args:
        access_token: Meta API access token (optional - will use cached token if not provided)
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        limit: Maximum number of campaigns to return (default: 10)
        status_filter: Filter by effective status (e.g., 'ACTIVE', 'PAUSED', 'ARCHIVED').
                       Maps to the 'effective_status' API parameter, which expects an array
                       (this function handles the required JSON formatting). Leave empty for all statuses.
        after: Pagination cursor to get the next set of results
    """
    # If no account ID is specified, try to get the first one for the user
    if not account_id:
        accounts_json = await get_ad_accounts("me", json.dumps({"limit": 1}), access_token)
        accounts_data = json.loads(accounts_json)
        
        if "data" in accounts_data and accounts_data["data"]:
            account_id = accounts_data["data"][0]["id"]
        else:
            return json.dumps({"error": "No account ID specified and no accounts found for user"}, indent=2)
    
    endpoint = f"{account_id}/campaigns"
    params = {
        "fields": "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy",
        "limit": limit
    }
    
    if status_filter:
        # API expects an array, encode it as a JSON string
        params["effective_status"] = json.dumps([status_filter])
    
    if after:
        params["after"] = after
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_campaign_details(access_token: str = None, campaign_id: str = None) -> str:
    """
    Get detailed information about a specific campaign.

    Note: This function requests a specific set of fields ('id,name,objective,status,...'). 
    The Meta API offers many other fields for campaigns (e.g., 'effective_status', 'source_campaign_id', etc.) 
    that could be added to the 'fields' parameter in the code if needed.
    
    Args:
        access_token: Meta API access token (optional - will use cached token if not provided)
        campaign_id: Meta Ads campaign ID
    """
    if not campaign_id:
        return json.dumps({"error": "No campaign ID provided"}, indent=2)
    
    endpoint = f"{campaign_id}"
    params = {
        "fields": "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy,special_ad_categories,special_ad_category_country,budget_remaining,configured_status"
    }
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def create_campaign(
    access_token: str = None,
    account_id: str = None,
    name: str = None,
    objective: str = None,
    status: str = "PAUSED",
    special_ad_categories: List[str] = None,
    daily_budget = None,
    lifetime_budget = None,
    buying_type: str = None,
    bid_strategy: str = None,
    bid_cap = None,
    spend_cap = None,
    campaign_budget_optimization: bool = None,
    ab_test_control_setups: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create a new campaign in a Meta Ads account.
    
    Args:
        access_token: Meta API access token (optional - will use cached token if not provided)
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        name: Campaign name
        objective: Campaign objective. Validates ad objectives. enum{BRAND_AWARENESS, LEAD_GENERATION, LINK_CLICKS, CONVERSIONS, OUTCOME_TRAFFIC, etc.}.
        status: Initial campaign status (default: PAUSED)
        special_ad_categories: List of special ad categories if applicable
        daily_budget: Daily budget in account currency (in cents) as a string
        lifetime_budget: Lifetime budget in account currency (in cents) as a string
        buying_type: Buying type (e.g., 'AUCTION')
        bid_strategy: Bid strategy (e.g., 'LOWEST_COST', 'LOWEST_COST_WITH_BID_CAP', 'COST_CAP')
        bid_cap: Bid cap in account currency (in cents) as a string
        spend_cap: Spending limit for the campaign in account currency (in cents) as a string
        campaign_budget_optimization: Whether to enable campaign budget optimization
        ab_test_control_setups: Settings for A/B testing (e.g., [{"name":"Creative A", "ad_format":"SINGLE_IMAGE"}])
    """
    # Check required parameters
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)
    
    if not name:
        return json.dumps({"error": "No campaign name provided"}, indent=2)
        
    if not objective:
        return json.dumps({"error": "No campaign objective provided"}, indent=2)
    
    # Special_ad_categories is required by the API, set default if not provided
    if special_ad_categories is None:
        special_ad_categories = []
    
    # For this example, we'll add a fixed daily budget if none is provided
    if not daily_budget and not lifetime_budget:
        daily_budget = "1000"  # Default to $10 USD
    
    endpoint = f"{account_id}/campaigns"
    
    params = {
        "name": name,
        "objective": objective,
        "status": status,
        "special_ad_categories": json.dumps(special_ad_categories)  # Properly format as JSON string
    }
    
    # Convert budget values to strings if they aren't already
    if daily_budget is not None:
        params["daily_budget"] = str(daily_budget)
    
    if lifetime_budget is not None:
        params["lifetime_budget"] = str(lifetime_budget)
    
    # Add new parameters
    if buying_type:
        params["buying_type"] = buying_type
    
    if bid_strategy:
        params["bid_strategy"] = bid_strategy
    
    if bid_cap is not None:
        params["bid_cap"] = str(bid_cap)
    
    if spend_cap is not None:
        params["spend_cap"] = str(spend_cap)
    
    if campaign_budget_optimization is not None:
        params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    
    if ab_test_control_setups:
        params["ab_test_control_setups"] = json.dumps(ab_test_control_setups)
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        return json.dumps({
            "error": "Failed to create campaign",
            "details": error_msg,
            "params_sent": params
        }, indent=2)


@mcp_server.tool()
@meta_api_tool
async def update_campaign(
    access_token: str = None,
    campaign_id: str = None,
    name: str = None,
    status: str = None,
    special_ad_categories: List[str] = None,
    daily_budget = None,
    lifetime_budget = None,
    bid_strategy: str = None,
    bid_cap = None,
    spend_cap = None,
    campaign_budget_optimization: bool = None,
    objective: str = None,  # Add objective if it's updatable
    # Add other updatable fields as needed based on API docs
) -> str:
    """
    Update an existing campaign in a Meta Ads account.

    Args:
        access_token: Meta API access token (optional - will use cached token if not provided)
        campaign_id: Meta Ads campaign ID (required)
        name: New campaign name
        status: New campaign status (e.g., 'ACTIVE', 'PAUSED')
        special_ad_categories: List of special ad categories if applicable
        daily_budget: New daily budget in account currency (in cents) as a string
        lifetime_budget: New lifetime budget in account currency (in cents) as a string
        bid_strategy: New bid strategy
        bid_cap: New bid cap in account currency (in cents) as a string
        spend_cap: New spending limit for the campaign in account currency (in cents) as a string
        campaign_budget_optimization: Enable/disable campaign budget optimization
        objective: New campaign objective (Note: May not always be updatable)
    """
    if not campaign_id:
        return json.dumps({"error": "No campaign ID provided"}, indent=2)

    endpoint = f"{campaign_id}"
    
    params = {}
    
    # Add parameters to the request only if they are provided
    if name is not None:
        params["name"] = name
    if status is not None:
        params["status"] = status
    if special_ad_categories is not None:
        # Note: Updating special_ad_categories might have specific API rules or might not be allowed after creation.
        # The API might require an empty list `[]` to clear categories. Check Meta Docs.
        params["special_ad_categories"] = json.dumps(special_ad_categories)
    if daily_budget is not None:
        params["daily_budget"] = str(daily_budget)
    if lifetime_budget is not None:
        params["lifetime_budget"] = str(lifetime_budget)
    if bid_strategy is not None:
        params["bid_strategy"] = bid_strategy
    if bid_cap is not None:
        params["bid_cap"] = str(bid_cap)
    if spend_cap is not None:
        params["spend_cap"] = str(spend_cap)
    if campaign_budget_optimization is not None:
        params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    if objective is not None:
        params["objective"] = objective # Caution: Objective changes might reset learning or be restricted

    if not params:
        return json.dumps({"error": "No update parameters provided"}, indent=2)

    try:
        # Use POST method for updates as per Meta API documentation
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        # Include campaign_id in error for better context
        return json.dumps({
            "error": f"Failed to update campaign {campaign_id}",
            "details": error_msg,
            "params_sent": params # Be careful about logging sensitive data if any
        }, indent=2) 
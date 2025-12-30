"""LangChain tools for agent capabilities."""

from typing import Optional, Dict, Any
from langchain.tools import tool
import logging

logger = logging.getLogger(__name__)


@tool
def get_branch_locations(city: str) -> str:
    """Get branch locations for a city.
    
    Args:
        city: City name
        
    Returns:
        Branch location information
    """
    # TODO: Integrate with actual branch database
    logger.info(f"Branch lookup requested for: {city}")
    
    # Mock response
    return f"We have multiple branches in {city}. For exact addresses and timings, please visit our website or I can connect you to customer service."


@tool
def check_service_hours() -> str:
    """Get current service hours and availability.
    
    Returns:
        Service hours information
    """
    logger.info("Service hours requested")
    
    return "Our customer service is available 24/7. Branch hours are Monday to Friday 10 AM to 4 PM, and Saturday 10 AM to 2 PM."


@tool
def get_product_information(product_type: str) -> str:
    """Get general information about a product type.
    
    Args:
        product_type: Type of product (savings account, credit card, loan, insurance, etc.)
        
    Returns:
        Product information
    """
    logger.info(f"Product info requested: {product_type}")
    
    # TODO: Integrate with product catalog
    product_info = {
        "savings account": "We offer various savings accounts with competitive interest rates and zero balance options. Would you like to know about specific account types?",
        "credit card": "We have credit cards for different needs - cashback, rewards, travel, and fuel. Interest rates start from 3.5% per month. Which category interests you?",
        "personal loan": "Personal loans are available from 10.5% per annum with flexible tenures. Eligibility depends on income and credit score. Would you like to check eligibility?",
        "home loan": "Home loans available at competitive rates starting from 8.5% per annum. We offer up to 90% financing. Shall I connect you to our home loan specialist?",
        "insurance": "We offer term insurance, health insurance, and investment-linked plans. Which type would you like to know about?",
    }
    
    return product_info.get(
        product_type.lower(),
        f"I can provide general information about {product_type}. For detailed features and pricing, I recommend speaking with our specialist. Would you like me to connect you?"
    )


@tool
def transfer_to_department(department: str, reason: str) -> str:
    """Transfer call to appropriate department.
    
    Args:
        department: Department name (customer_service, claims, loans, etc.)
        reason: Reason for transfer
        
    Returns:
        Transfer confirmation message
    """
    logger.info(f"Transfer requested to {department}: {reason}")
    
    # TODO: Integrate with actual call transfer system
    return f"I'm transferring you to our {department} team who can better assist you with {reason}. Please hold."


@tool
def schedule_callback(preferred_time: str, topic: str) -> str:
    """Schedule a callback for the customer.
    
    Args:
        preferred_time: Customer's preferred callback time
        topic: Topic for callback
        
    Returns:
        Callback confirmation
    """
    logger.info(f"Callback scheduled for {preferred_time} regarding {topic}")
    
    # TODO: Integrate with callback scheduling system
    return f"I've scheduled a callback for {preferred_time} regarding {topic}. Our team will reach out to you. Is there anything else I can help with?"


# Tool list for agent
BFSI_TOOLS = [
    get_branch_locations,
    check_service_hours,
    get_product_information,
    transfer_to_department,
    schedule_callback,
]


def get_tools_for_persona(persona: str) -> list:
    """Get appropriate tools for agent persona.
    
    Args:
        persona: Agent persona (bank, insurance, financial_services)
        
    Returns:
        List of tools
    """
    # All personas get base tools
    # Can be extended with persona-specific tools
    return BFSI_TOOLS

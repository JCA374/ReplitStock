from config import (
    PE_LOW_THRESHOLD,
    PE_HIGH_THRESHOLD,
    PROFIT_MARGIN_THRESHOLD,
    REVENUE_GROWTH_THRESHOLD
)

def analyze_pe_ratio(pe_ratio):
    """
    Analyze P/E ratio.
    
    Returns:
        dict: Analysis with status and description
    """
    if pe_ratio is None or pe_ratio <= 0:
        return {
            'status': 'unknown',
            'description': 'P/E ratio not available or negative (potential losses)'
        }
    
    if pe_ratio < PE_LOW_THRESHOLD:
        return {
            'status': 'undervalued',
            'description': f'P/E ratio ({pe_ratio:.2f}) below {PE_LOW_THRESHOLD} suggests potential undervaluation'
        }
    elif pe_ratio > PE_HIGH_THRESHOLD:
        return {
            'status': 'overvalued',
            'description': f'P/E ratio ({pe_ratio:.2f}) above {PE_HIGH_THRESHOLD} suggests potential overvaluation'
        }
    else:
        return {
            'status': 'fair',
            'description': f'P/E ratio ({pe_ratio:.2f}) within fair value range'
        }

def analyze_profit_margin(profit_margin):
    """
    Analyze profit margin.
    
    Returns:
        dict: Analysis with status and description
    """
    if profit_margin is None:
        return {
            'status': 'unknown',
            'description': 'Profit margin data not available'
        }
    
    if profit_margin < 0:
        return {
            'status': 'negative',
            'description': f'Negative profit margin ({profit_margin:.2%}) indicates losses'
        }
    elif profit_margin < PROFIT_MARGIN_THRESHOLD:
        return {
            'status': 'low',
            'description': f'Profit margin ({profit_margin:.2%}) below threshold ({PROFIT_MARGIN_THRESHOLD:.2%})'
        }
    else:
        return {
            'status': 'good',
            'description': f'Healthy profit margin ({profit_margin:.2%})'
        }

def analyze_revenue_growth(revenue_growth):
    """
    Analyze revenue growth.
    
    Returns:
        dict: Analysis with status and description
    """
    if revenue_growth is None:
        return {
            'status': 'unknown',
            'description': 'Revenue growth data not available'
        }
    
    if revenue_growth < 0:
        return {
            'status': 'declining',
            'description': f'Declining revenue ({revenue_growth:.2%})'
        }
    elif revenue_growth < REVENUE_GROWTH_THRESHOLD:
        return {
            'status': 'slow',
            'description': f'Slow revenue growth ({revenue_growth:.2%})'
        }
    else:
        return {
            'status': 'growing',
            'description': f'Strong revenue growth ({revenue_growth:.2%})'
        }

def analyze_fundamentals(fundamentals):
    """
    Perform a comprehensive fundamental analysis based on all available metrics.
    
    Args:
        fundamentals (dict): Dictionary containing fundamental metrics
        
    Returns:
        dict: Comprehensive analysis results
    """
    if not fundamentals:
        return {
            'overall': {
                'status': 'unknown',
                'description': 'Fundamental data not available'
            }
        }
    
    analysis = {}
    
    # Analyze individual metrics
    analysis['pe_ratio'] = analyze_pe_ratio(fundamentals.get('pe_ratio'))
    analysis['profit_margin'] = analyze_profit_margin(fundamentals.get('profit_margin'))
    analysis['revenue_growth'] = analyze_revenue_growth(fundamentals.get('revenue_growth'))
    
    # Count positive and negative factors
    positive_factors = 0
    negative_factors = 0
    total_factors = 0
    
    # Check P/E ratio
    if analysis['pe_ratio']['status'] == 'undervalued':
        positive_factors += 1
    elif analysis['pe_ratio']['status'] == 'overvalued':
        negative_factors += 1
    if analysis['pe_ratio']['status'] != 'unknown':
        total_factors += 1
    
    # Check profit margin
    if analysis['profit_margin']['status'] == 'good':
        positive_factors += 1
    elif analysis['profit_margin']['status'] in ['negative', 'low']:
        negative_factors += 1
    if analysis['profit_margin']['status'] != 'unknown':
        total_factors += 1
    
    # Check revenue growth
    if analysis['revenue_growth']['status'] == 'growing':
        positive_factors += 1
    elif analysis['revenue_growth']['status'] in ['declining', 'slow']:
        negative_factors += 1
    if analysis['revenue_growth']['status'] != 'unknown':
        total_factors += 1
    
    # Calculate overall sentiment
    if total_factors == 0:
        overall_status = 'unknown'
        overall_description = 'Insufficient fundamental data for analysis'
    else:
        score = positive_factors - negative_factors
        
        if score > 0:
            overall_status = 'positive'
            overall_description = f'{positive_factors}/{total_factors} positive factors suggest favorable fundamentals'
        elif score < 0:
            overall_status = 'negative'
            overall_description = f'{negative_factors}/{total_factors} negative factors suggest concerning fundamentals'
        else:
            overall_status = 'neutral'
            overall_description = 'Mixed or neutral fundamental indicators'
    
    analysis['overall'] = {
        'status': overall_status,
        'description': overall_description,
        'positive_factors': positive_factors,
        'negative_factors': negative_factors,
        'total_factors': total_factors
    }
    
    return analysis

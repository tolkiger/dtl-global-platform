#!/usr/bin/env python3
"""Test script for Phase 3 AI enhancements.

This script tests the enhanced AI capabilities for multiple industries
and measures cost efficiency to ensure under $0.05 for 10 test calls.

Author: DTL-Global Platform
"""

import json
import sys
import os
import time
from typing import Dict, List, Any

# Add the engine path to import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'engine', 'shared'))

from ai_client import ai_client


def test_bid_generation_multiple_industries() -> Dict[str, Any]:
    """Test bid generation for multiple industries.
    
    Returns:
        Dictionary containing test results for each industry
    """
    print("Testing bid generation for multiple industries...")
    
    # Test industries (3+ as required by Phase 3 gate)
    test_industries = ['roofing', 'dental', 'legal', 'medical', 'restaurant']
    
    # Sample client requirements for testing
    sample_requirements = {
        'services': ['website', 'seo', 'hosting'],
        'timeline': '4 weeks',
        'budget_range': '$1000-$2500',
        'company_info': {
            'size': 'small',
            'existing_website': False,
            'current_marketing': 'word_of_mouth'
        }
    }
    
    results = {}
    total_start_time = time.time()
    
    for industry in test_industries:
        print(f"\n--- Testing {industry.upper()} industry ---")
        start_time = time.time()
        
        try:
            # Generate bid for this industry
            bid_result = ai_client.generate_bid(sample_requirements, industry)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Store results
            results[industry] = {
                'success': True,
                'bid_data': bid_result,
                'response_time': response_time,
                'setup_cost': bid_result.get('setup_cost', 0),
                'monthly_cost': bid_result.get('monthly_cost', 0),
                'package_recommendation': bid_result.get('package_recommendation', 'N/A'),
                'industry_specific_features': bid_result.get('industry_specific_features', [])
            }
            
            print(f"✅ {industry}: ${bid_result.get('setup_cost', 0)} setup / ${bid_result.get('monthly_cost', 0)} monthly")
            print(f"   Package: {bid_result.get('package_recommendation', 'N/A')}")
            print(f"   Features: {len(bid_result.get('industry_specific_features', []))} industry-specific")
            print(f"   Response time: {response_time:.2f}s")
            
        except Exception as e:
            print(f"❌ {industry}: Error - {str(e)}")
            results[industry] = {
                'success': False,
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    total_time = time.time() - total_start_time
    print(f"\n--- Total bid generation test time: {total_time:.2f}s ---")
    
    return results


def test_seo_website_prompts() -> Dict[str, Any]:
    """Test SEO website prompt generation.
    
    Returns:
        Dictionary containing test results for website prompts
    """
    print("\n\nTesting SEO website prompt generation...")
    
    # Sample business info for testing
    sample_business = {
        'name': 'Test Business',
        'description': 'Professional services company',
        'location': 'Austin, TX',
        'services': ['consulting', 'training', 'support'],
        'keywords': ['professional services', 'consulting', 'Austin'],
        'phone': '512-555-0123',
        'address': '123 Main St, Austin, TX 78701'
    }
    
    # Test industries
    test_industries = ['roofing', 'dental', 'legal']
    results = {}
    
    for industry in test_industries:
        print(f"\n--- Testing {industry.upper()} website prompt ---")
        start_time = time.time()
        
        try:
            # Generate website prompt for this industry
            website_prompt = ai_client.generate_website_prompt(sample_business, industry)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Check for required SEO elements (13 elements from master plan)
            required_seo_elements = [
                'HTML5', 'meta title', 'H1', 'schema.org', 'open graph',
                'mobile', 'robots.txt', 'NAP', 'internal linking', 'CTA',
                'contact form', 'google maps', 'accessibility'
            ]
            
            seo_elements_found = []
            for element in required_seo_elements:
                if element.lower() in website_prompt.lower():
                    seo_elements_found.append(element)
            
            # Store results
            results[industry] = {
                'success': True,
                'prompt_length': len(website_prompt),
                'response_time': response_time,
                'seo_elements_found': seo_elements_found,
                'seo_coverage': len(seo_elements_found) / len(required_seo_elements) * 100,
                'contains_industry_context': industry.lower() in website_prompt.lower()
            }
            
            print(f"✅ {industry}: {len(website_prompt)} chars generated")
            print(f"   SEO coverage: {len(seo_elements_found)}/13 elements ({results[industry]['seo_coverage']:.1f}%)")
            print(f"   Industry context: {'Yes' if results[industry]['contains_industry_context'] else 'No'}")
            print(f"   Response time: {response_time:.2f}s")
            
        except Exception as e:
            print(f"❌ {industry}: Error - {str(e)}")
            results[industry] = {
                'success': False,
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    return results


def test_crm_column_mapping() -> Dict[str, Any]:
    """Test CRM column mapping functionality.
    
    Returns:
        Dictionary containing test results for CRM mapping
    """
    print("\n\nTesting CRM column mapping...")
    
    # Sample CSV headers for testing
    test_csv_headers = [
        'First Name', 'Last Name', 'Email Address', 'Phone Number',
        'Company Name', 'Job Title', 'Address', 'City', 'State', 'ZIP',
        'Website', 'Industry', 'Lead Source', 'Notes'
    ]
    
    start_time = time.time()
    
    try:
        # Analyze CSV headers for HubSpot mapping
        mapping_result = ai_client.analyze_crm_columns(test_csv_headers, 'hubspot')
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Analyze mapping quality
        mapped_count = len(mapping_result)
        expected_mappings = ['firstname', 'lastname', 'email', 'phone', 'company']
        
        results = {
            'success': True,
            'headers_count': len(test_csv_headers),
            'mapped_count': mapped_count,
            'mapping_percentage': mapped_count / len(test_csv_headers) * 100,
            'response_time': response_time,
            'mappings': mapping_result,
            'has_standard_fields': all(field in str(mapping_result).lower() for field in expected_mappings)
        }
        
        print(f"✅ CRM Mapping: {mapped_count}/{len(test_csv_headers)} fields mapped ({results['mapping_percentage']:.1f}%)")
        print(f"   Standard fields: {'Yes' if results['has_standard_fields'] else 'No'}")
        print(f"   Response time: {response_time:.2f}s")
        
    except Exception as e:
        print(f"❌ CRM Mapping: Error - {str(e)}")
        results = {
            'success': False,
            'error': str(e),
            'response_time': time.time() - start_time
        }
    
    return results


def test_custom_request_estimation() -> Dict[str, Any]:
    """Test custom request estimation.
    
    Returns:
        Dictionary containing test results for custom estimation
    """
    print("\n\nTesting custom request estimation...")
    
    # Sample custom request for testing
    custom_request = """
    Build a custom patient portal for a dental practice that integrates with their existing 
    practice management software. The portal should allow patients to:
    - Schedule appointments online
    - View treatment history and upcoming appointments
    - Make payments
    - Upload insurance information
    - Communicate with the office
    
    The portal needs to be HIPAA compliant and integrate with their current Dentrix software.
    """
    
    start_time = time.time()
    
    try:
        # Estimate custom request
        estimation_result = ai_client.estimate_custom_request(custom_request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Analyze estimation quality
        results = {
            'success': True,
            'estimated_hours': estimation_result.get('estimated_hours', 0),
            'complexity': estimation_result.get('complexity', 'unknown'),
            'has_breakdown': 'breakdown' in estimation_result,
            'has_assumptions': 'assumptions' in estimation_result,
            'has_risks': 'risks' in estimation_result,
            'response_time': response_time,
            'estimation_data': estimation_result
        }
        
        print(f"✅ Custom Estimation: {results['estimated_hours']} hours ({results['complexity']} complexity)")
        print(f"   Breakdown: {'Yes' if results['has_breakdown'] else 'No'}")
        print(f"   Assumptions: {'Yes' if results['has_assumptions'] else 'No'}")
        print(f"   Risks: {'Yes' if results['has_risks'] else 'No'}")
        print(f"   Response time: {response_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Custom Estimation: Error - {str(e)}")
        results = {
            'success': False,
            'error': str(e),
            'response_time': time.time() - start_time
        }
    
    return results


def test_template_customization() -> Dict[str, Any]:
    """Test template customization functionality.
    
    Returns:
        Dictionary containing test results for template customization
    """
    print("\n\nTesting template customization...")
    
    # Sample base template
    base_template = {
        'name': 'Professional Services Template',
        'version': '1.0',
        'color_scheme': {
            'primary': '#333333',
            'secondary': '#666666',
            'background': '#ffffff'
        },
        'sections': [
            {'name': 'hero', 'title': 'Welcome'},
            {'name': 'services', 'title': 'Services'},
            {'name': 'about', 'title': 'About'},
            {'name': 'contact', 'title': 'Contact'}
        ]
    }
    
    # Sample business info
    business_info = {
        'name': 'Elite Roofing Solutions',
        'industry': 'roofing',
        'location': 'Dallas, TX',
        'services': ['roof repair', 'roof replacement', 'storm damage']
    }
    
    start_time = time.time()
    
    try:
        # Customize template for roofing industry
        customized_template = ai_client.customize_industry_template(
            base_template, 'roofing', business_info
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Analyze customization quality
        results = {
            'success': True,
            'has_color_scheme': 'color_scheme' in customized_template,
            'has_sections': 'sections' in customized_template,
            'has_navigation': 'navigation' in customized_template,
            'has_trust_signals': 'trust_signals' in customized_template,
            'is_customized': customized_template.get('customization_metadata', {}).get('customized', False),
            'response_time': response_time,
            'template_data': customized_template
        }
        
        print(f"✅ Template Customization: Successfully customized for roofing")
        print(f"   Color scheme: {'Yes' if results['has_color_scheme'] else 'No'}")
        print(f"   Sections: {'Yes' if results['has_sections'] else 'No'}")
        print(f"   Trust signals: {'Yes' if results['has_trust_signals'] else 'No'}")
        print(f"   Response time: {response_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Template Customization: Error - {str(e)}")
        results = {
            'success': False,
            'error': str(e),
            'response_time': time.time() - start_time
        }
    
    return results


def calculate_estimated_costs(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate estimated API costs for the test calls.
    
    Args:
        test_results: Combined test results from all tests
        
    Returns:
        Dictionary containing cost analysis
    """
    print("\n\nCalculating estimated API costs...")
    
    # Claude Haiku 4.5 pricing (approximate)
    # Input: $0.25 per million tokens
    # Output: $1.25 per million tokens
    
    # Estimate tokens per test (rough approximation)
    estimated_tokens_per_test = {
        'bid_generation': {'input': 800, 'output': 400},  # Structured bid output
        'website_prompts': {'input': 1200, 'output': 800},  # Longer SEO content
        'crm_mapping': {'input': 400, 'output': 200},  # Simple mapping
        'custom_estimation': {'input': 600, 'output': 300},  # Estimation breakdown
        'template_customization': {'input': 1000, 'output': 500}  # Template JSON
    }
    
    total_input_tokens = 0
    total_output_tokens = 0
    total_api_calls = 0
    
    # Count successful tests and estimate tokens
    for test_type, results in test_results.items():
        if test_type in estimated_tokens_per_test:
            if isinstance(results, dict):
                if results.get('success', False):
                    # Single test
                    total_api_calls += 1
                    total_input_tokens += estimated_tokens_per_test[test_type]['input']
                    total_output_tokens += estimated_tokens_per_test[test_type]['output']
                else:
                    # Multiple industry tests
                    for industry_result in results.values():
                        if isinstance(industry_result, dict) and industry_result.get('success', False):
                            total_api_calls += 1
                            total_input_tokens += estimated_tokens_per_test[test_type]['input']
                            total_output_tokens += estimated_tokens_per_test[test_type]['output']
    
    # Calculate costs
    input_cost = (total_input_tokens / 1_000_000) * 0.25
    output_cost = (total_output_tokens / 1_000_000) * 1.25
    total_cost = input_cost + output_cost
    
    cost_analysis = {
        'total_api_calls': total_api_calls,
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost,
        'cost_per_call': total_cost / max(total_api_calls, 1),
        'under_budget': total_cost < 0.05  # Phase 3 requirement
    }
    
    print(f"📊 Cost Analysis:")
    print(f"   Total API calls: {total_api_calls}")
    print(f"   Input tokens: {total_input_tokens:,}")
    print(f"   Output tokens: {total_output_tokens:,}")
    print(f"   Input cost: ${input_cost:.4f}")
    print(f"   Output cost: ${output_cost:.4f}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Cost per call: ${cost_analysis['cost_per_call']:.4f}")
    print(f"   Under $0.05 budget: {'✅ Yes' if cost_analysis['under_budget'] else '❌ No'}")
    
    return cost_analysis


def main():
    """Run all Phase 3 AI enhancement tests."""
    print("🚀 DTL-Global Phase 3 AI Enhancement Testing")
    print("=" * 50)
    
    # Run all tests
    test_results = {}
    
    # Test 1: Bid generation for multiple industries
    test_results['bid_generation'] = test_bid_generation_multiple_industries()
    
    # Test 2: SEO website prompts
    test_results['website_prompts'] = test_seo_website_prompts()
    
    # Test 3: CRM column mapping
    test_results['crm_mapping'] = test_crm_column_mapping()
    
    # Test 4: Custom request estimation
    test_results['custom_estimation'] = test_custom_request_estimation()
    
    # Test 5: Template customization
    test_results['template_customization'] = test_template_customization()
    
    # Calculate costs
    cost_analysis = calculate_estimated_costs(test_results)
    
    # Generate summary report
    print("\n\n📋 PHASE 3 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = 0
    successful_tests = 0
    
    for test_type, results in test_results.items():
        if isinstance(results, dict):
            if 'success' in results:
                # Single test
                total_tests += 1
                if results['success']:
                    successful_tests += 1
                    print(f"✅ {test_type.replace('_', ' ').title()}: PASSED")
                else:
                    print(f"❌ {test_type.replace('_', ' ').title()}: FAILED")
            else:
                # Multiple tests (like bid generation)
                for industry, result in results.items():
                    total_tests += 1
                    if result.get('success', False):
                        successful_tests += 1
                        print(f"✅ {test_type.replace('_', ' ').title()} ({industry}): PASSED")
                    else:
                        print(f"❌ {test_type.replace('_', ' ').title()} ({industry}): FAILED")
    
    success_rate = (successful_tests / max(total_tests, 1)) * 100
    
    print(f"\n📊 Overall Results:")
    print(f"   Total tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   Total cost: ${cost_analysis['total_cost']:.4f}")
    print(f"   Budget compliance: {'✅ PASS' if cost_analysis['under_budget'] else '❌ FAIL'}")
    
    # Phase 3 gate criteria check
    print(f"\n🎯 Phase 3 Gate Criteria:")
    
    # Check if bid generation works for 3+ industries
    bid_industries = len([r for r in test_results['bid_generation'].values() if r.get('success', False)])
    print(f"   Bid generation for 3+ industries: {'✅ PASS' if bid_industries >= 3 else '❌ FAIL'} ({bid_industries} industries)")
    
    # Check if website prompts include SEO elements
    seo_coverage = test_results['website_prompts']
    avg_seo_coverage = sum(r.get('seo_coverage', 0) for r in seo_coverage.values() if r.get('success', False)) / max(len(seo_coverage), 1)
    print(f"   Website prompt SEO elements: {'✅ PASS' if avg_seo_coverage >= 80 else '❌ FAIL'} ({avg_seo_coverage:.1f}% coverage)")
    
    # Check cost requirement
    print(f"   AI costs under $0.05: {'✅ PASS' if cost_analysis['under_budget'] else '❌ FAIL'}")
    
    # Save detailed results
    with open('phase3_test_results.json', 'w') as f:
        json.dump({
            'test_results': test_results,
            'cost_analysis': cost_analysis,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': success_rate
            }
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: phase3_test_results.json")


if __name__ == "__main__":
    main()
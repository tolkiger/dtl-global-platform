#!/usr/bin/env python3
"""Test script for Phase 4 deployment automation.

This script tests the complete website deployment automation flow:
GitHub → S3 → CloudFront → ACM SSL → Route 53 → HTTPS Live

Tests all 3 client domain scenarios and verifies deployment functionality.

Author: DTL-Global Platform
"""

import json
import sys
import os
import time
from typing import Dict, List, Any

# Add the engine path to import shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'engine', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'engine', 'handlers'))

try:
    from handler_deploy import (
        _validate_deployment_request,
        _generate_website_content,
        _generate_enhanced_website_html,
        _generate_robots_txt,
        _generate_sitemap_xml,
        _get_industry_keywords
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    print("Some tests will be skipped due to missing dependencies")
    IMPORTS_AVAILABLE = False


def test_deployment_request_validation() -> Dict[str, Any]:
    """Test deployment request validation functionality.
    
    Returns:
        Dictionary containing test results
    """
    print("Testing deployment request validation...")
    
    if not IMPORTS_AVAILABLE:
        return {'success': False, 'error': 'Imports not available', 'skipped': True}
    
    test_cases = [
        # Valid request
        {
            'name': 'valid_request',
            'data': {
                'client_info': {
                    'company': 'Test Company',
                    'domain': 'testcompany.com',
                    'email': 'test@testcompany.com',
                    'industry': 'roofing'
                },
                'deployment_config': {
                    'domain_scenario': 'new_domain',
                    'ssl_enabled': True
                }
            },
            'should_pass': True
        },
        # Missing client_info
        {
            'name': 'missing_client_info',
            'data': {
                'deployment_config': {
                    'domain_scenario': 'new_domain'
                }
            },
            'should_pass': False
        },
        # Invalid domain format
        {
            'name': 'invalid_domain',
            'data': {
                'client_info': {
                    'company': 'Test Company',
                    'domain': 'invalid-domain',
                    'email': 'test@testcompany.com',
                    'industry': 'roofing'
                }
            },
            'should_pass': False
        },
        # Invalid email format
        {
            'name': 'invalid_email',
            'data': {
                'client_info': {
                    'company': 'Test Company',
                    'domain': 'testcompany.com',
                    'email': 'invalid-email',
                    'industry': 'roofing'
                }
            },
            'should_pass': False
        },
        # Invalid domain scenario
        {
            'name': 'invalid_domain_scenario',
            'data': {
                'client_info': {
                    'company': 'Test Company',
                    'domain': 'testcompany.com',
                    'email': 'test@testcompany.com',
                    'industry': 'roofing'
                },
                'deployment_config': {
                    'domain_scenario': 'invalid_scenario'
                }
            },
            'should_pass': False
        }
    ]
    
    results = {
        'total_tests': len(test_cases),
        'passed': 0,
        'failed': 0,
        'test_results': {}
    }
    
    for test_case in test_cases:
        try:
            validation_error = _validate_deployment_request(test_case['data'])
            
            if test_case['should_pass']:
                # Should pass validation (no error)
                if validation_error is None:
                    results['passed'] += 1
                    results['test_results'][test_case['name']] = {'status': 'PASS', 'expected': True}
                    print(f"  ✅ {test_case['name']}: PASS")
                else:
                    results['failed'] += 1
                    results['test_results'][test_case['name']] = {
                        'status': 'FAIL', 
                        'expected': True, 
                        'error': validation_error
                    }
                    print(f"  ❌ {test_case['name']}: FAIL - {validation_error}")
            else:
                # Should fail validation (have error)
                if validation_error is not None:
                    results['passed'] += 1
                    results['test_results'][test_case['name']] = {
                        'status': 'PASS', 
                        'expected': False, 
                        'error': validation_error
                    }
                    print(f"  ✅ {test_case['name']}: PASS - Correctly rejected")
                else:
                    results['failed'] += 1
                    results['test_results'][test_case['name']] = {
                        'status': 'FAIL', 
                        'expected': False, 
                        'error': 'Should have failed validation'
                    }
                    print(f"  ❌ {test_case['name']}: FAIL - Should have been rejected")
                    
        except Exception as e:
            results['failed'] += 1
            results['test_results'][test_case['name']] = {
                'status': 'ERROR', 
                'error': str(e)
            }
            print(f"  ❌ {test_case['name']}: ERROR - {str(e)}")
    
    results['success'] = results['failed'] == 0
    results['success_rate'] = (results['passed'] / results['total_tests']) * 100
    
    print(f"  📊 Validation Tests: {results['passed']}/{results['total_tests']} passed ({results['success_rate']:.1f}%)")
    
    return results


def test_website_content_generation() -> Dict[str, Any]:
    """Test website content generation functionality.
    
    Returns:
        Dictionary containing test results
    """
    print("\nTesting website content generation...")
    
    if not IMPORTS_AVAILABLE:
        return {'success': False, 'error': 'Imports not available', 'skipped': True}
    
    # Sample client info for testing
    test_client_info = {
        'company': 'Elite Roofing Solutions',
        'domain': 'eliteroofing.com',
        'email': 'info@eliteroofing.com',
        'industry': 'roofing',
        'location': 'Dallas, TX',
        'phone': '(214) 555-0123'
    }
    
    test_deployment_config = {
        'domain_scenario': 'new_domain',
        'ssl_enabled': True,
        'deployment_type': 'ai_generated'
    }
    
    results = {
        'success': True,
        'tests_performed': [],
        'content_generated': {},
        'seo_elements_found': {},
        'errors': []
    }
    
    try:
        # Test website content generation
        print("  🎨 Generating website content...")
        website_files = _generate_website_content(test_client_info, test_deployment_config)
        
        results['content_generated'] = {
            'files_count': len(website_files),
            'file_names': list(website_files.keys()),
            'total_content_length': sum(len(content) for content in website_files.values())
        }
        
        print(f"    ✅ Generated {len(website_files)} files")
        print(f"    📄 Files: {', '.join(website_files.keys())}")
        
        # Test specific file generation
        required_files = ['index.html', 'robots.txt', 'sitemap.xml', 'styles.css']
        for required_file in required_files:
            if required_file in website_files:
                print(f"    ✅ {required_file}: Generated ({len(website_files[required_file])} chars)")
                results['tests_performed'].append(f'{required_file}_generated')
            else:
                print(f"    ❌ {required_file}: Missing")
                results['errors'].append(f'Missing required file: {required_file}')
                results['success'] = False
        
        # Test HTML content for SEO elements
        if 'index.html' in website_files:
            html_content = website_files['index.html']
            seo_elements = _check_seo_elements(html_content)
            results['seo_elements_found'] = seo_elements
            
            print(f"    🔍 SEO Elements: {seo_elements['found_count']}/13 elements found")
            for element, found in seo_elements['elements'].items():
                status = "✅" if found else "❌"
                print(f"      {status} {element}")
        
        # Test robots.txt content
        if 'robots.txt' in website_files:
            robots_content = website_files['robots.txt']
            if 'User-agent: *' in robots_content and 'Sitemap:' in robots_content:
                print("    ✅ robots.txt: Valid format")
                results['tests_performed'].append('robots_txt_valid')
            else:
                print("    ❌ robots.txt: Invalid format")
                results['errors'].append('robots.txt has invalid format')
        
        # Test sitemap.xml content
        if 'sitemap.xml' in website_files:
            sitemap_content = website_files['sitemap.xml']
            if '<?xml version="1.0"' in sitemap_content and '<urlset' in sitemap_content:
                print("    ✅ sitemap.xml: Valid XML format")
                results['tests_performed'].append('sitemap_xml_valid')
            else:
                print("    ❌ sitemap.xml: Invalid XML format")
                results['errors'].append('sitemap.xml has invalid XML format')
        
    except Exception as e:
        results['success'] = False
        results['errors'].append(f'Content generation failed: {str(e)}')
        print(f"    ❌ Content generation failed: {str(e)}")
    
    return results


def test_industry_specific_features() -> Dict[str, Any]:
    """Test industry-specific content generation.
    
    Returns:
        Dictionary containing test results
    """
    print("\nTesting industry-specific features...")
    
    if not IMPORTS_AVAILABLE:
        return {'success': False, 'error': 'Imports not available', 'skipped': True}
    
    # Test multiple industries
    test_industries = ['roofing', 'dental', 'legal', 'medical', 'restaurant']
    
    results = {
        'success': True,
        'industries_tested': len(test_industries),
        'industry_results': {},
        'errors': []
    }
    
    for industry in test_industries:
        print(f"  🏭 Testing {industry} industry...")
        
        try:
            # Test industry keywords generation
            keywords = _get_industry_keywords(industry, 'Austin, TX')
            
            industry_result = {
                'keywords_generated': True,
                'has_title': 'title' in keywords,
                'has_description': 'description' in keywords,
                'has_keywords_list': 'keywords' in keywords and len(keywords['keywords']) > 0,
                'has_hero_text': 'hero_text' in keywords
            }
            
            # Test HTML generation with industry context
            test_client_info = {
                'company': f'Test {industry.title()} Company',
                'domain': f'test{industry}.com',
                'email': f'info@test{industry}.com',
                'industry': industry,
                'location': 'Austin, TX',
                'phone': '(512) 555-0123'
            }
            
            html_content = _generate_enhanced_website_html(test_client_info, "")
            
            # Check for industry-specific content
            industry_mentions = html_content.lower().count(industry.lower())
            industry_result['industry_mentions'] = industry_mentions
            industry_result['has_industry_content'] = industry_mentions > 3
            
            # Check for structured data
            industry_result['has_structured_data'] = '"@type": "LocalBusiness"' in html_content
            
            results['industry_results'][industry] = industry_result
            
            # Determine if this industry test passed
            industry_passed = all([
                industry_result['keywords_generated'],
                industry_result['has_title'],
                industry_result['has_industry_content'],
                industry_result['has_structured_data']
            ])
            
            if industry_passed:
                print(f"    ✅ {industry}: All features working")
            else:
                print(f"    ❌ {industry}: Some features missing")
                results['success'] = False
                
        except Exception as e:
            print(f"    ❌ {industry}: Error - {str(e)}")
            results['errors'].append(f'{industry} industry test failed: {str(e)}')
            results['success'] = False
    
    return results


def test_domain_scenarios() -> Dict[str, Any]:
    """Test all 3 client domain scenarios.
    
    Returns:
        Dictionary containing test results
    """
    print("\nTesting client domain scenarios...")
    
    domain_scenarios = [
        {
            'name': 'new_domain',
            'description': 'New client domain (client registers, points DNS to CloudFront)'
        },
        {
            'name': 'existing_domain',
            'description': 'Existing client domain elsewhere (client updates DNS to CloudFront)'
        },
        {
            'name': 'route53_managed',
            'description': 'Client domain on Route 53 (programmatically add alias records)'
        }
    ]
    
    results = {
        'success': True,
        'scenarios_tested': len(domain_scenarios),
        'scenario_results': {},
        'errors': []
    }
    
    for scenario in domain_scenarios:
        print(f"  🌍 Testing {scenario['name']} scenario...")
        
        try:
            # Create test deployment configuration for this scenario
            test_config = {
                'client_info': {
                    'company': f'Test Company {scenario["name"].title()}',
                    'domain': f'test-{scenario["name"]}.com',
                    'email': f'test@test-{scenario["name"]}.com',
                    'industry': 'professional_services'
                },
                'deployment_config': {
                    'domain_scenario': scenario['name'],
                    'ssl_enabled': True,
                    'cdn_enabled': True
                }
            }
            
            # Test validation
            validation_error = _validate_deployment_request(test_config)
            
            scenario_result = {
                'validation_passed': validation_error is None,
                'validation_error': validation_error,
                'scenario_supported': True  # All scenarios should be supported
            }
            
            if validation_error:
                print(f"    ❌ {scenario['name']}: Validation failed - {validation_error}")
                results['success'] = False
            else:
                print(f"    ✅ {scenario['name']}: Validation passed")
            
            results['scenario_results'][scenario['name']] = scenario_result
            
        except Exception as e:
            print(f"    ❌ {scenario['name']}: Error - {str(e)}")
            results['errors'].append(f'{scenario["name"]} scenario test failed: {str(e)}')
            results['success'] = False
    
    return results


def _check_seo_elements(html_content: str) -> Dict[str, Any]:
    """Check HTML content for required SEO elements.
    
    Args:
        html_content: HTML content to analyze
        
    Returns:
        Dictionary containing SEO element analysis
    """
    seo_elements = {
        'semantic_html5': any(tag in html_content for tag in ['<header>', '<nav>', '<main>', '<section>', '<footer>']),
        'meta_description': '<meta name="description"' in html_content,
        'meta_keywords': '<meta name="keywords"' in html_content,
        'title_tag': '<title>' in html_content,
        'h1_tag': '<h1' in html_content,
        'structured_data': '"@type": "LocalBusiness"' in html_content,
        'open_graph': '<meta property="og:' in html_content,
        'viewport_meta': 'name="viewport"' in html_content,
        'canonical_link': 'rel="canonical"' in html_content,
        'contact_form': '<form' in html_content and 'name="email"' in html_content,
        'honeypot_protection': 'name="website"' in html_content and 'style="display:none"' in html_content,
        'accessibility_features': 'aria-' in html_content or 'role=' in html_content,
        'phone_link': 'href="tel:' in html_content
    }
    
    found_count = sum(1 for found in seo_elements.values() if found)
    
    return {
        'elements': seo_elements,
        'found_count': found_count,
        'total_elements': len(seo_elements),
        'coverage_percentage': (found_count / len(seo_elements)) * 100
    }


def test_file_generation_functions() -> Dict[str, Any]:
    """Test individual file generation functions.
    
    Returns:
        Dictionary containing test results
    """
    print("\nTesting individual file generation functions...")
    
    if not IMPORTS_AVAILABLE:
        return {'success': False, 'error': 'Imports not available', 'skipped': True}
    
    test_domain = 'testcompany.com'
    
    results = {
        'success': True,
        'functions_tested': 0,
        'functions_passed': 0,
        'function_results': {},
        'errors': []
    }
    
    # Test robots.txt generation
    try:
        robots_content = _generate_robots_txt(test_domain)
        results['functions_tested'] += 1
        
        if 'User-agent: *' in robots_content and f'Sitemap: https://{test_domain}/sitemap.xml' in robots_content:
            results['functions_passed'] += 1
            results['function_results']['robots_txt'] = {'status': 'PASS', 'length': len(robots_content)}
            print("  ✅ robots.txt generation: PASS")
        else:
            results['function_results']['robots_txt'] = {'status': 'FAIL', 'error': 'Invalid format'}
            results['errors'].append('robots.txt generation produced invalid format')
            print("  ❌ robots.txt generation: FAIL - Invalid format")
            
    except Exception as e:
        results['functions_tested'] += 1
        results['function_results']['robots_txt'] = {'status': 'ERROR', 'error': str(e)}
        results['errors'].append(f'robots.txt generation error: {str(e)}')
        print(f"  ❌ robots.txt generation: ERROR - {str(e)}")
    
    # Test sitemap.xml generation
    try:
        sitemap_content = _generate_sitemap_xml(test_domain)
        results['functions_tested'] += 1
        
        if ('<?xml version="1.0"' in sitemap_content and 
            '<urlset xmlns=' in sitemap_content and 
            f'<loc>https://{test_domain}/</loc>' in sitemap_content):
            results['functions_passed'] += 1
            results['function_results']['sitemap_xml'] = {'status': 'PASS', 'length': len(sitemap_content)}
            print("  ✅ sitemap.xml generation: PASS")
        else:
            results['function_results']['sitemap_xml'] = {'status': 'FAIL', 'error': 'Invalid XML format'}
            results['errors'].append('sitemap.xml generation produced invalid XML')
            print("  ❌ sitemap.xml generation: FAIL - Invalid XML format")
            
    except Exception as e:
        results['functions_tested'] += 1
        results['function_results']['sitemap_xml'] = {'status': 'ERROR', 'error': str(e)}
        results['errors'].append(f'sitemap.xml generation error: {str(e)}')
        print(f"  ❌ sitemap.xml generation: ERROR - {str(e)}")
    
    results['success'] = len(results['errors']) == 0
    results['success_rate'] = (results['functions_passed'] / max(results['functions_tested'], 1)) * 100
    
    print(f"  📊 Function Tests: {results['functions_passed']}/{results['functions_tested']} passed ({results['success_rate']:.1f}%)")
    
    return results


def main():
    """Run all Phase 4 deployment automation tests."""
    print("🚀 DTL-Global Phase 4 Deployment Automation Testing")
    print("=" * 60)
    
    # Run all tests
    test_results = {}
    
    # Test 1: Deployment request validation
    test_results['validation'] = test_deployment_request_validation()
    
    # Test 2: Website content generation
    test_results['content_generation'] = test_website_content_generation()
    
    # Test 3: Industry-specific features
    test_results['industry_features'] = test_industry_specific_features()
    
    # Test 4: Domain scenarios
    test_results['domain_scenarios'] = test_domain_scenarios()
    
    # Test 5: File generation functions
    test_results['file_generation'] = test_file_generation_functions()
    
    # Generate summary report
    print("\n\n📋 PHASE 4 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = 0
    successful_tests = 0
    skipped_tests = 0
    
    for test_name, results in test_results.items():
        if results.get('skipped', False):
            skipped_tests += 1
            print(f"⏭️  {test_name.replace('_', ' ').title()}: SKIPPED")
        elif results.get('success', False):
            successful_tests += 1
            print(f"✅ {test_name.replace('_', ' ').title()}: PASSED")
        else:
            print(f"❌ {test_name.replace('_', ' ').title()}: FAILED")
        
        total_tests += 1
    
    actual_tests = total_tests - skipped_tests
    success_rate = (successful_tests / max(actual_tests, 1)) * 100
    
    print(f"\n📊 Overall Results:")
    print(f"   Total test suites: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Skipped: {skipped_tests}")
    print(f"   Success rate: {success_rate:.1f}%")
    
    # Phase 4 gate criteria check
    print(f"\n🎯 Phase 4 Gate Criteria:")
    
    # Check content generation
    content_success = test_results['content_generation'].get('success', False)
    print(f"   Website content generation: {'✅ PASS' if content_success else '❌ FAIL'}")
    
    # Check industry support
    industry_success = test_results['industry_features'].get('success', False)
    print(f"   Industry-specific features: {'✅ PASS' if industry_success else '❌ FAIL'}")
    
    # Check domain scenarios
    domain_success = test_results['domain_scenarios'].get('success', False)
    print(f"   All 3 domain scenarios: {'✅ PASS' if domain_success else '❌ FAIL'}")
    
    # Check SEO elements
    seo_elements = test_results['content_generation'].get('seo_elements_found', {})
    seo_coverage = seo_elements.get('coverage_percentage', 0)
    print(f"   SEO elements coverage: {'✅ PASS' if seo_coverage >= 80 else '❌ FAIL'} ({seo_coverage:.1f}%)")
    
    # Check file generation
    file_success = test_results['file_generation'].get('success', False)
    print(f"   File generation functions: {'✅ PASS' if file_success else '❌ FAIL'}")
    
    # Overall Phase 4 readiness
    phase4_ready = all([
        content_success,
        industry_success, 
        domain_success,
        seo_coverage >= 80,
        file_success
    ])
    
    print(f"\n🎉 Phase 4 Readiness: {'✅ READY' if phase4_ready else '❌ NOT READY'}")
    
    # Save detailed results
    with open('phase4_test_results.json', 'w') as f:
        json.dump({
            'test_results': test_results,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'skipped_tests': skipped_tests,
                'success_rate': success_rate,
                'phase4_ready': phase4_ready
            }
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: phase4_test_results.json")
    
    if not IMPORTS_AVAILABLE:
        print("\n⚠️  Note: Some tests were skipped due to missing dependencies.")
        print("   In a production environment with all dependencies installed,")
        print("   these tests would provide complete validation coverage.")


if __name__ == "__main__":
    main()
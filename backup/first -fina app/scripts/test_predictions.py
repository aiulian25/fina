#!/usr/bin/env python3
"""
Test script for predictions feature
Run inside the container or with the same Python environment
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_predictions_import():
    """Test that predictions module can be imported"""
    try:
        from app.predictions import (
            get_spending_predictions,
            predict_category_spending,
            generate_insights,
            get_category_forecast,
            get_seasonal_factor,
            compare_with_predictions
        )
        print("✅ All prediction functions imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_seasonal_factor():
    """Test seasonal factor calculations"""
    from app.predictions import get_seasonal_factor
    from datetime import datetime
    
    tests = [
        (datetime(2024, 12, 15), 1.15, "December (holidays)"),
        (datetime(2024, 1, 15), 0.90, "January (post-holiday)"),
        (datetime(2024, 7, 15), 1.05, "July (summer)"),
        (datetime(2024, 3, 15), 1.0, "March (normal)"),
    ]
    
    all_passed = True
    for date, expected, description in tests:
        result = get_seasonal_factor(date)
        if result == expected:
            print(f"✅ {description}: {result}")
        else:
            print(f"❌ {description}: Expected {expected}, got {result}")
            all_passed = False
    
    return all_passed

def test_translation_keys():
    """Test that all prediction translation keys exist"""
    from app.translations import translations
    
    required_keys = [
        'predictions.title',
        'predictions.subtitle',
        'predictions.confidence_high',
        'predictions.confidence_medium',
        'predictions.confidence_low',
        'predictions.trend_increasing',
        'predictions.trend_decreasing',
        'predictions.trend_stable',
        'predictions.no_data',
        'predictions.insights',
    ]
    
    all_passed = True
    for lang in ['en', 'ro', 'es']:
        missing = []
        for key in required_keys:
            if key not in translations.get(lang, {}):
                missing.append(key)
        
        if missing:
            print(f"❌ {lang.upper()}: Missing keys: {', '.join(missing)}")
            all_passed = False
        else:
            print(f"✅ {lang.upper()}: All translation keys present")
    
    return all_passed

def test_routes_exist():
    """Test that prediction routes are registered"""
    try:
        from app import create_app
        app = create_app()
        
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        required_routes = [
            '/predictions',
            '/api/predictions',
            '/api/predictions/category/<int:category_id>'
        ]
        
        all_passed = True
        for route in required_routes:
            # Check if route pattern exists (exact match or with converter)
            found = any(route.replace('<int:category_id>', '<category_id>') in r or route in r 
                       for r in routes)
            if found:
                print(f"✅ Route registered: {route}")
            else:
                print(f"❌ Route missing: {route}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"❌ Route check failed: {e}")
        return False

def test_template_exists():
    """Test that predictions template exists"""
    template_path = os.path.join(
        os.path.dirname(__file__),
        'app', 'templates', 'predictions.html'
    )
    
    if os.path.exists(template_path):
        print(f"✅ Template exists: {template_path}")
        
        # Check for key elements
        with open(template_path, 'r') as f:
            content = f.read()
            checks = [
                ('predictions.title', 'Title translation'),
                ('predictionsChart', 'Chart element'),
                ('showCategoryForecast', 'Forecast function'),
                ('confidence', 'Confidence badges'),
            ]
            
            all_passed = True
            for check, description in checks:
                if check in content:
                    print(f"  ✅ {description}")
                else:
                    print(f"  ❌ {description} missing")
                    all_passed = False
            
            return all_passed
    else:
        print(f"❌ Template not found: {template_path}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PREDICTIONS FEATURE TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        ("Module Import", test_predictions_import),
        ("Seasonal Factors", test_seasonal_factor),
        ("Translation Keys", test_translation_keys),
        ("Route Registration", test_routes_exist),
        ("Template Existence", test_template_exists),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    for name, passed_flag in results:
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Feature is ready for manual testing.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

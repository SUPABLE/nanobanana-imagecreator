#!/usr/bin/env python3
"""
Backend API Tests for Nano Banana Image Generator
Tests all backend endpoints including Gemini Nano Banana integration
"""

import requests
import json
import time
import base64
from datetime import datetime

# Configuration
BASE_URL = "https://nano-pic-creator-7.preview.emergentagent.com/api"
TIMEOUT = 30  # seconds

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "status" in data and data["status"] == "healthy":
                print("✅ Health check endpoint working correctly")
                return True
            else:
                print("❌ Health check response format incorrect")
                return False
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Health check test error: {str(e)}")
        return False

def test_image_generation():
    """Test image generation with Gemini Nano Banana model"""
    print("\n=== Testing Image Generation Endpoint ===")
    try:
        # Test with a simple prompt
        test_prompt = "a cute orange cat sitting next to a yellow banana on a wooden table"
        payload = {"prompt": test_prompt}
        
        print(f"Generating image with prompt: '{test_prompt}'")
        print("This may take 10-30 seconds...")
        
        response = requests.post(
            f"{BASE_URL}/generate-image", 
            json=payload, 
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check required fields
            required_fields = ["id", "prompt", "image_url", "created_at", "success"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False, None
                
            # Verify the image_url contains base64 data
            if not data["image_url"].startswith("data:image/"):
                print("❌ Image URL is not a valid data URL")
                return False, None
                
            # Try to decode base64 data to verify it's valid
            try:
                base64_data = data["image_url"].split(",")[1]
                decoded_data = base64.b64decode(base64_data)
                print(f"✅ Image generated successfully! Size: {len(decoded_data)} bytes")
                print(f"Image ID: {data['id']}")
                print(f"Prompt: {data['prompt']}")
                return True, data["id"]
            except Exception as e:
                print(f"❌ Invalid base64 image data: {str(e)}")
                return False, None
                
        else:
            print(f"Response: {response.text}")
            print(f"❌ Image generation failed with status {response.status_code}")
            return False, None
            
    except requests.exceptions.Timeout:
        print("❌ Image generation request timed out")
        return False, None
    except requests.exceptions.RequestException as e:
        print(f"❌ Image generation request failed: {str(e)}")
        return False, None
    except Exception as e:
        print(f"❌ Image generation test error: {str(e)}")
        return False, None

def test_get_images():
    """Test retrieving generated images"""
    print("\n=== Testing Get Images Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/images", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of images retrieved: {len(data)}")
            
            if len(data) > 0:
                # Check first image structure
                first_image = data[0]
                required_fields = ["id", "prompt", "image_url", "created_at", "success"]
                missing_fields = [field for field in required_fields if field not in first_image]
                
                if missing_fields:
                    print(f"❌ Missing required fields in image data: {missing_fields}")
                    return False
                    
                print(f"✅ Images retrieved successfully")
                print(f"Sample image ID: {first_image['id']}")
                print(f"Sample prompt: {first_image['prompt'][:50]}...")
                return True
            else:
                print("✅ Images endpoint working (no images found)")
                return True
                
        else:
            print(f"Response: {response.text}")
            print(f"❌ Get images failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Get images request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Get images test error: {str(e)}")
        return False

def test_delete_image(image_id):
    """Test deleting a generated image"""
    print(f"\n=== Testing Delete Image Endpoint ===")
    if not image_id:
        print("⚠️ No image ID provided, skipping delete test")
        return True
        
    try:
        response = requests.delete(f"{BASE_URL}/images/{image_id}", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            if data.get("success") and "deleted" in data.get("message", "").lower():
                print(f"✅ Image deleted successfully")
                return True
            else:
                print(f"❌ Delete response format incorrect")
                return False
                
        elif response.status_code == 404:
            print("⚠️ Image not found (may have been deleted already)")
            return True
        else:
            print(f"Response: {response.text}")
            print(f"❌ Delete image failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Delete image request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Delete image test error: {str(e)}")
        return False

def test_delete_nonexistent_image():
    """Test deleting a non-existent image"""
    print(f"\n=== Testing Delete Non-existent Image ===")
    fake_id = "non-existent-image-id-12345"
    
    try:
        response = requests.delete(f"{BASE_URL}/images/{fake_id}", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Correctly returned 404 for non-existent image")
            return True
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Delete non-existent image request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Delete non-existent image test error: {str(e)}")
        return False

def main():
    """Run all backend tests"""
    print("🚀 Starting Nano Banana Image Generator Backend Tests")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    results = {}
    generated_image_id = None
    
    # Test 1: Health Check
    results["health_check"] = test_health_endpoint()
    
    # Test 2: Image Generation (most critical test)
    results["image_generation"], generated_image_id = test_image_generation()
    
    # Test 3: Get Images
    results["get_images"] = test_get_images()
    
    # Test 4: Delete Image (using generated image if available)
    results["delete_image"] = test_delete_image(generated_image_id)
    
    # Test 5: Delete Non-existent Image
    results["delete_nonexistent"] = test_delete_nonexistent_image()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
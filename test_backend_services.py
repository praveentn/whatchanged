# test_backend_services.py
"""
DocuReview Pro - Comprehensive Backend Testing Script
Tests all backend services and endpoints independently
"""

import asyncio
import json
import time
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendTester:
    """Comprehensive backend testing suite for DocuReview Pro"""
    
    def __init__(self, base_url: str = "http://localhost:8555"):
        """
        Initialize the backend tester
        
        Args:
            base_url (str): Base URL of the running application
        """
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Test data storage
        self.test_documents = []
        self.test_comparisons = []
        
        # Test results
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": {}
        }

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        
        if success:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {details}")
        
        self.results["details"][test_name] = {
            "success": success,
            "details": details,
            "timestamp": time.time()
        }

    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "headers": dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "data": {}
            }
        except json.JSONDecodeError as e:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": {"raw_content": response.text},
                "json_error": str(e)
            }

    # Health Check Tests
    def test_health_check(self):
        """Test application health endpoint"""
        response = self.make_request("GET", "/health")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            response["data"].get("status") == "healthy"
        )
        
        self.log_test(
            "Health Check",
            success,
            f"Status: {response.get('status_code')}, Data: {response.get('data')}"
        )
        return success

    # Document Management Tests
    def test_document_upload(self):
        """Test document upload functionality"""
        # Create test document content
        test_content = """# System Requirements Document v1.0

## Introduction
This document outlines the requirements for the new customer portal system.

## Functional Requirements
The system must support:
- User authentication and authorization
- Real-time data synchronization
- Multi-language support

## Non-Functional Requirements
Performance requirements:
- Response time < 2 seconds
- 99.9% uptime
- Support 10,000 concurrent users

## Security Requirements
- Data encryption at rest and in transit
- Regular security audits
- Compliance with GDPR

## Implementation Details
1. Use Python FastAPI for backend
2. Implement React frontend
3. Use PostgreSQL database
4. Deploy on AWS infrastructure

## Conclusion
These requirements form the foundation for system development.
"""
        
        # Create file-like object
        files = {
            'file': ('test_document.txt', io.StringIO(test_content), 'text/plain')
        }
        
        data = {
            'title': 'System Requirements Document',
            'author': 'Test Author',
            'domain': 'technical',
            'tags': 'requirements,system,documentation',
            'notes': 'Test document for backend validation',
            'auto_analyze': 'true'
        }
        
        response = self.make_request("POST", "/api/documents/upload", files=files, data=data)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            response["data"].get("success") == True
        )
        
        if success and response["data"].get("document"):
            self.test_documents.append(response["data"]["document"])
        
        self.log_test(
            "Document Upload",
            success,
            f"Status: {response.get('status_code')}, Response: {response.get('data', {}).get('message', 'No message')}"
        )
        return success

    def test_document_upload_version2(self):
        """Test uploading a second version of the same document"""
        # Modified content for version 2
        test_content_v2 = """# System Requirements Document v2.0

## Introduction
This document outlines the enhanced requirements for the new customer portal system with additional features.

## Functional Requirements
The system must support:
- User authentication and authorization with OAuth 2.0
- Real-time data synchronization with WebSocket support
- Multi-language support with 15+ languages
- Advanced reporting and analytics
- Mobile application support

## Non-Functional Requirements
Enhanced performance requirements:
- Response time < 1 second
- 99.99% uptime
- Support 50,000 concurrent users
- Auto-scaling capabilities

## Security Requirements
- Data encryption at rest and in transit with AES-256
- Regular security audits and penetration testing
- Compliance with GDPR, CCPA, and SOX
- Multi-factor authentication
- Role-based access control

## Implementation Details
1. Use Python FastAPI with async support
2. Implement React frontend with TypeScript
3. Use PostgreSQL with read replicas
4. Deploy on AWS with Kubernetes
5. Implement CI/CD pipeline
6. Add monitoring and alerting

## New Features
- AI-powered recommendations
- Advanced search capabilities
- Integration with third-party services
- Real-time collaboration tools

## Conclusion
These enhanced requirements will create a world-class customer portal system.
"""
        
        files = {
            'file': ('test_document_v2.txt', io.StringIO(test_content_v2), 'text/plain')
        }
        
        data = {
            'title': 'System Requirements Document',  # Same title for versioning
            'author': 'Test Author',
            'domain': 'technical',
            'tags': 'requirements,system,documentation,enhanced',
            'notes': 'Enhanced version with additional features',
            'auto_analyze': 'true'
        }
        
        response = self.make_request("POST", "/api/documents/upload", files=files, data=data)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            response["data"].get("success") == True
        )
        
        if success and response["data"].get("document"):
            self.test_documents.append(response["data"]["document"])
        
        self.log_test(
            "Document Upload Version 2",
            success,
            f"Status: {response.get('status_code')}, Version: {response.get('data', {}).get('document', {}).get('version', 'N/A')}"
        )
        return success

    def test_list_documents(self):
        """Test document listing with pagination and filters"""
        response = self.make_request("GET", "/api/documents/", params={
            "limit": 20,
            "offset": 0,
            "search": "system"
        })
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "documents" in response["data"]
        )
        
        self.log_test(
            "List Documents",
            success,
            f"Status: {response.get('status_code')}, Documents found: {len(response.get('data', {}).get('documents', []))}"
        )
        return success

    def test_get_document_detail(self):
        """Test getting detailed document information"""
        if not self.test_documents:
            self.log_test("Get Document Detail", False, "No test documents available")
            return False
        
        doc_id = self.test_documents[0]["id"]
        response = self.make_request("GET", f"/api/documents/{doc_id}", params={
            "include_content": "true",
            "include_analysis": "true"
        })
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            response["data"].get("id") == doc_id
        )
        
        self.log_test(
            "Get Document Detail",
            success,
            f"Status: {response.get('status_code')}, Doc ID: {doc_id}"
        )
        return success

    def test_document_versions(self):
        """Test getting document versions"""
        if not self.test_documents:
            self.log_test("Document Versions", False, "No test documents available")
            return False
        
        slug = self.test_documents[0]["slug"]
        response = self.make_request("GET", f"/api/documents/slug/{slug}/versions")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "versions" in response["data"]
        )
        
        self.log_test(
            "Document Versions",
            success,
            f"Status: {response.get('status_code')}, Versions: {len(response.get('data', {}).get('versions', []))}"
        )
        return success

    def test_document_analysis(self):
        """Test document analysis endpoint"""
        if not self.test_documents:
            self.log_test("Document Analysis", False, "No test documents available")
            return False
        
        doc_id = self.test_documents[0]["id"]
        
        # First trigger analysis if not already done
        analysis_request = {
            "force_reanalysis": False
        }
        
        response = self.make_request("POST", f"/api/documents/{doc_id}/analyze", json=analysis_request)
        
        # Wait a moment for analysis to process
        time.sleep(2)
        
        # Get analysis results
        response = self.make_request("GET", f"/api/documents/{doc_id}/analysis")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "document_info" in response["data"]
        )
        
        self.log_test(
            "Document Analysis",
            success,
            f"Status: {response.get('status_code')}, Analysis available: {'document_info' in response.get('data', {})}"
        )
        return success

    def test_document_stats(self):
        """Test document statistics"""
        if not self.test_documents:
            self.log_test("Document Stats", False, "No test documents available")
            return False
        
        doc_id = self.test_documents[0]["id"]
        response = self.make_request("GET", f"/api/documents/{doc_id}/stats")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "document_info" in response["data"]
        )
        
        self.log_test(
            "Document Stats",
            success,
            f"Status: {response.get('status_code')}, Stats available: {'content_stats' in response.get('data', {})}"
        )
        return success

    # Comparison Tests
    def test_document_comparison(self):
        """Test document version comparison"""
        if len(self.test_documents) < 2:
            self.log_test("Document Comparison", False, "Need at least 2 documents for comparison")
            return False
        
        comparison_request = {
            "document_a_id": self.test_documents[0]["id"],
            "document_b_id": self.test_documents[1]["id"],
            "granularity": "word",
            "algorithm": "hybrid",
            "similarity_threshold": 0.8,
            "show_only_changes": False,
            "color_scheme": "default"
        }
        
        response = self.make_request("POST", "/api/comparison/compare", json=comparison_request)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "metrics" in response["data"]
        )
        
        if success:
            self.test_comparisons.append(response["data"])
        
        self.log_test(
            "Document Comparison",
            success,
            f"Status: {response.get('status_code')}, Similarity: {response.get('data', {}).get('metrics', {}).get('overall_similarity', 'N/A')}"
        )
        return success

    def test_comparison_by_slug(self):
        """Test comparison by document slug and versions"""
        if len(self.test_documents) < 2:
            self.log_test("Comparison by Slug", False, "Need at least 2 document versions")
            return False
        
        slug = self.test_documents[0]["slug"]
        comparison_request = {
            "document_slug": slug,
            "version_a": 1,
            "version_b": 2,
            "granularity": "sentence",
            "algorithm": "semantic",
            "similarity_threshold": 0.7
        }
        
        response = self.make_request("POST", "/api/comparison/compare-by-slug", json=comparison_request)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "metrics" in response["data"]
        )
        
        self.log_test(
            "Comparison by Slug",
            success,
            f"Status: {response.get('status_code')}, Algorithm used: {response.get('data', {}).get('document_info', {}).get('comparison_config', {}).get('algorithm', 'N/A')}"
        )
        return success

    def test_comparison_algorithms(self):
        """Test getting available comparison algorithms"""
        response = self.make_request("GET", "/api/comparison/algorithms")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "granularities" in response["data"] and
            "algorithms" in response["data"]
        )
        
        self.log_test(
            "Comparison Algorithms",
            success,
            f"Status: {response.get('status_code')}, Algorithms: {len(response.get('data', {}).get('algorithms', []))}"
        )
        return success

    def test_diff_configurations(self):
        """Test diff configuration management"""
        # Get existing configurations
        response = self.make_request("GET", "/api/comparison/configurations")
        
        get_success = (
            response["success"] and 
            response["status_code"] == 200 and
            "configurations" in response["data"]
        )
        
        # Create new configuration
        new_config = {
            "name": "Test Configuration",
            "granularity": "word",
            "algorithm": "hybrid",
            "color_scheme": "default",
            "similarity_threshold": 0.85,
            "show_only_changes": False,
            "is_default": False
        }
        
        create_response = self.make_request("POST", "/api/comparison/configurations", json=new_config)
        
        create_success = (
            create_response["success"] and 
            create_response["status_code"] == 200 and
            create_response["data"].get("success") == True
        )
        
        overall_success = get_success and create_success
        
        self.log_test(
            "Diff Configurations",
            overall_success,
            f"Get Status: {response.get('status_code')}, Create Status: {create_response.get('status_code')}"
        )
        return overall_success

    # Search Tests
    def test_semantic_search(self):
        """Test semantic search functionality"""
        if not self.test_documents:
            self.log_test("Semantic Search", False, "No test documents available")
            return False
        
        search_request = {
            "query": "authentication security requirements",
            "document_slug": self.test_documents[0]["slug"],
            "search_type": "semantic",
            "top_k": 10,
            "similarity_threshold": 0.5
        }
        
        response = self.make_request("POST", "/api/search/semantic", json=search_request)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "results" in response["data"]
        )
        
        self.log_test(
            "Semantic Search",
            success,
            f"Status: {response.get('status_code')}, Results: {len(response.get('data', {}).get('results', []))}"
        )
        return success

    def test_global_search(self):
        """Test global search across all documents"""
        search_request = {
            "query": "system requirements",
            "search_scope": "all",
            "top_k": 20
        }
        
        response = self.make_request("POST", "/api/search/global", json=search_request)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "results" in response["data"]
        )
        
        self.log_test(
            "Global Search",
            success,
            f"Status: {response.get('status_code')}, Results: {len(response.get('data', {}).get('results', []))}"
        )
        return success

    def test_search_suggestions(self):
        """Test search suggestions"""
        response = self.make_request("GET", "/api/search/suggestions", params={
            "query": "auth",
            "limit": 5
        })
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "suggestions" in response["data"]
        )
        
        self.log_test(
            "Search Suggestions",
            success,
            f"Status: {response.get('status_code')}, Suggestions: {len(response.get('data', {}).get('suggestions', []))}"
        )
        return success

    def test_search_stats(self):
        """Test search statistics"""
        response = self.make_request("GET", "/api/search/stats")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "indexing_stats" in response["data"]
        )
        
        self.log_test(
            "Search Stats",
            success,
            f"Status: {response.get('status_code')}, Stats available: {'content_distribution' in response.get('data', {})}"
        )
        return success

    # Admin Tests
    def test_sql_executor(self):
        """Test SQL executor functionality"""
        # Test simple SELECT query
        sql_request = {
            "query": "SELECT COUNT(*) as total_documents FROM documents",
            "limit_results": True
        }
        
        response = self.make_request("POST", "/api/admin/sql/execute", json=sql_request)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            response["data"].get("success") == True
        )
        
        self.log_test(
            "SQL Executor",
            success,
            f"Status: {response.get('status_code')}, Query executed: {response.get('data', {}).get('query_type', 'Unknown')}"
        )
        return success

    def test_database_schema(self):
        """Test getting database schema"""
        response = self.make_request("GET", "/api/admin/sql/schema")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "tables" in response["data"]
        )
        
        self.log_test(
            "Database Schema",
            success,
            f"Status: {response.get('status_code')}, Tables: {len(response.get('data', {}).get('tables', []))}"
        )
        return success

    def test_system_stats(self):
        """Test system statistics"""
        response = self.make_request("GET", "/api/admin/stats/system")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "application" in response["data"] and
            "database" in response["data"]
        )
        
        self.log_test(
            "System Stats",
            success,
            f"Status: {response.get('status_code')}, App name: {response.get('data', {}).get('application', {}).get('name', 'N/A')}"
        )
        return success

    def test_audit_logs(self):
        """Test audit logs retrieval"""
        response = self.make_request("GET", "/api/admin/audit/logs", params={
            "limit": 50,
            "offset": 0
        })
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            "logs" in response["data"]
        )
        
        self.log_test(
            "Audit Logs",
            success,
            f"Status: {response.get('status_code')}, Logs: {len(response.get('data', {}).get('logs', []))}"
        )
        return success

    def test_maintenance_operations(self):
        """Test maintenance operations (dry run)"""
        maintenance_request = {
            "operation": "cleanup_old_comparisons",
            "parameters": {"days_old": 30},
            "dry_run": True
        }
        
        response = self.make_request("POST", "/api/admin/maintenance", json=maintenance_request)
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            response["data"].get("success") == True
        )
        
        self.log_test(
            "Maintenance Operations",
            success,
            f"Status: {response.get('status_code')}, Operation: {response.get('data', {}).get('operation', 'N/A')}"
        )
        return success

    def test_backup_creation(self):
        """Test database backup creation"""
        response = self.make_request("GET", "/api/admin/backup/create")
        
        success = (
            response["success"] and 
            response["status_code"] == 200 and
            response["data"].get("success") == True
        )
        
        self.log_test(
            "Backup Creation",
            success,
            f"Status: {response.get('status_code')}, Backup created: {response.get('data', {}).get('backup_file', 'N/A')}"
        )
        return success

    # Comprehensive Test Runner
    def run_all_tests(self):
        """Run all backend tests in logical order"""
        logger.info("🚀 Starting DocuReview Pro Backend Testing Suite")
        logger.info(f"📡 Testing against: {self.base_url}")
        logger.info("=" * 60)
        
        # Test sequence with dependencies
        test_sequence = [
            # Basic connectivity
            self.test_health_check,
            
            # Document management
            self.test_document_upload,
            self.test_document_upload_version2,
            self.test_list_documents,
            self.test_get_document_detail,
            self.test_document_versions,
            self.test_document_analysis,
            self.test_document_stats,
            
            # Comparison functionality
            self.test_document_comparison,
            self.test_comparison_by_slug,
            self.test_comparison_algorithms,
            self.test_diff_configurations,
            
            # Search functionality
            self.test_semantic_search,
            self.test_global_search,
            self.test_search_suggestions,
            self.test_search_stats,
            
            # Admin functionality
            self.test_sql_executor,
            self.test_database_schema,
            self.test_system_stats,
            self.test_audit_logs,
            self.test_maintenance_operations,
            self.test_backup_creation,
        ]
        
        logger.info(f"📋 Running {len(test_sequence)} test modules...\n")
        
        # Execute tests
        for i, test_func in enumerate(test_sequence, 1):
            test_name = test_func.__name__.replace('test_', '').replace('_', ' ').title()
            logger.info(f"🧪 [{i:2d}/{len(test_sequence)}] {test_name}")
            
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        total_tests = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Tests Passed: {self.results['passed']}")
        logger.info(f"❌ Tests Failed: {self.results['failed']}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.results["errors"]:
            logger.info("\n🚨 FAILED TESTS:")
            for error in self.results["errors"]:
                logger.error(f"   • {error}")
        
        if self.test_documents:
            logger.info(f"\n📄 Test Documents Created: {len(self.test_documents)}")
            for doc in self.test_documents:
                logger.info(f"   • {doc['title']} v{doc['version']} (ID: {doc['id']})")
        
        if self.test_comparisons:
            logger.info(f"\n🔍 Comparisons Performed: {len(self.test_comparisons)}")
        
        # Overall result
        if success_rate >= 90:
            logger.info("\n🎉 EXCELLENT! Backend is working well.")
        elif success_rate >= 75:
            logger.info("\n👍 GOOD! Most features are working.")
        elif success_rate >= 50:
            logger.info("\n⚠️  PARTIAL! Some issues need attention.")
        else:
            logger.info("\n🚨 CRITICAL! Major issues detected.")
        
        logger.info("=" * 60)

def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DocuReview Pro Backend Testing Suite")
    parser.add_argument("--url", default="http://localhost:8555", help="Backend URL (default: http://localhost:8555)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize and run tests
    tester = BackendTester(base_url=args.url)
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\n🛑 Testing interrupted by user")
    except Exception as e:
        logger.error(f"\n💥 Testing failed with exception: {e}")
    
    return tester.results

if __name__ == "__main__":
    results = main()
    
    # Exit with appropriate code
    exit_code = 0 if results["failed"] == 0 else 1
    exit(exit_code)
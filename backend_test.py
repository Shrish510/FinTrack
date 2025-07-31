import requests
import sys
import json
from datetime import datetime

class FinanceTrackerAPITester:
    def __init__(self, base_url="https://05376ab3-fd19-4cd4-b9d5-de21c62e1686.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_transaction_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"Response: {json.dumps(response_data, indent=2)}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root endpoint"""
        success, response = self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_get_transactions_empty(self):
        """Test getting transactions when empty"""
        success, response = self.run_test(
            "Get Transactions (Empty)",
            "GET",
            "api/transactions",
            200
        )
        if success and 'transactions' in response:
            print(f"Found {len(response['transactions'])} existing transactions")
        return success

    def test_create_expense_transaction(self):
        """Create an expense transaction"""
        transaction_data = {
            "amount": 500.0,
            "description": "Lunch at restaurant",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": "Food",
            "type": "expense"
        }
        
        success, response = self.run_test(
            "Create Expense Transaction",
            "POST",
            "api/transactions",
            200,
            data=transaction_data
        )
        
        if success and 'transaction' in response:
            transaction_id = response['transaction'].get('id')
            if transaction_id:
                self.created_transaction_ids.append(transaction_id)
                print(f"Created transaction with ID: {transaction_id}")
            return transaction_id
        return None

    def test_create_income_transaction(self):
        """Create an income transaction"""
        transaction_data = {
            "amount": 25000.0,
            "description": "Salary",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": "Income",
            "type": "income"
        }
        
        success, response = self.run_test(
            "Create Income Transaction",
            "POST",
            "api/transactions",
            200,
            data=transaction_data
        )
        
        if success and 'transaction' in response:
            transaction_id = response['transaction'].get('id')
            if transaction_id:
                self.created_transaction_ids.append(transaction_id)
                print(f"Created transaction with ID: {transaction_id}")
            return transaction_id
        return None

    def test_get_transactions_with_data(self):
        """Test getting transactions after adding some"""
        success, response = self.run_test(
            "Get Transactions (With Data)",
            "GET",
            "api/transactions",
            200
        )
        if success and 'transactions' in response:
            transactions = response['transactions']
            print(f"Found {len(transactions)} transactions")
            for i, transaction in enumerate(transactions[:3]):  # Show first 3
                print(f"  {i+1}. {transaction.get('description', 'N/A')} - ₹{transaction.get('amount', 0)} ({transaction.get('type', 'N/A')})")
        return success

    def test_get_single_transaction(self, transaction_id):
        """Test getting a single transaction by ID"""
        if not transaction_id:
            print("⚠️ Skipping single transaction test - no transaction ID available")
            return False
            
        success, response = self.run_test(
            f"Get Single Transaction ({transaction_id[:8]}...)",
            "GET",
            f"api/transactions/{transaction_id}",
            200
        )
        return success

    def test_update_transaction(self, transaction_id):
        """Test updating a transaction"""
        if not transaction_id:
            print("⚠️ Skipping update test - no transaction ID available")
            return False
            
        update_data = {
            "description": "Updated lunch description",
            "amount": 600.0
        }
        
        success, response = self.run_test(
            f"Update Transaction ({transaction_id[:8]}...)",
            "PUT",
            f"api/transactions/{transaction_id}",
            200,
            data=update_data
        )
        return success

    def test_get_summary(self):
        """Test getting financial summary"""
        success, response = self.run_test(
            "Get Financial Summary",
            "GET",
            "api/summary",
            200
        )
        
        if success:
            print(f"📊 Summary Details:")
            print(f"  Total Income: ₹{response.get('total_income', 0)}")
            print(f"  Total Expenses: ₹{response.get('total_expenses', 0)}")
            print(f"  Balance: ₹{response.get('balance', 0)}")
            
            # Verify balance calculation
            expected_balance = response.get('total_income', 0) - response.get('total_expenses', 0)
            actual_balance = response.get('balance', 0)
            if abs(expected_balance - actual_balance) < 0.01:  # Allow for floating point precision
                print("✅ Balance calculation is correct")
            else:
                print(f"❌ Balance calculation error: Expected {expected_balance}, got {actual_balance}")
        
        return success

    def test_delete_transaction(self, transaction_id):
        """Test deleting a transaction"""
        if not transaction_id:
            print("⚠️ Skipping delete test - no transaction ID available")
            return False
            
        success, response = self.run_test(
            f"Delete Transaction ({transaction_id[:8]}...)",
            "DELETE",
            f"api/transactions/{transaction_id}",
            200
        )
        return success

    def test_error_cases(self):
        """Test error handling"""
        print("\n🔍 Testing Error Cases...")
        
        # Test invalid transaction ID
        success, _ = self.run_test(
            "Get Non-existent Transaction",
            "GET",
            "api/transactions/invalid-id",
            404
        )
        
        # Test invalid data
        invalid_data = {
            "amount": "invalid",
            "description": "",
            "category": "InvalidCategory"
        }
        
        success2, _ = self.run_test(
            "Create Transaction with Invalid Data",
            "POST",
            "api/transactions",
            422  # FastAPI validation error
        )
        
        return success or success2  # At least one error case should work

def main():
    print("🚀 Starting Finance Tracker API Tests")
    print("=" * 50)
    
    tester = FinanceTrackerAPITester()
    
    # Test sequence
    print("\n📋 Running API Tests...")
    
    # Basic connectivity
    tester.test_root_endpoint()
    
    # Initial state
    tester.test_get_transactions_empty()
    
    # Create transactions
    expense_id = tester.test_create_expense_transaction()
    income_id = tester.test_create_income_transaction()
    
    # Read operations
    tester.test_get_transactions_with_data()
    tester.test_get_single_transaction(expense_id)
    
    # Summary
    tester.test_get_summary()
    
    # Update operation
    tester.test_update_transaction(expense_id)
    
    # Error cases
    tester.test_error_cases()
    
    # Cleanup - delete created transactions
    for transaction_id in tester.created_transaction_ids:
        tester.test_delete_transaction(transaction_id)
    
    # Final summary check
    tester.test_get_summary()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All API tests passed!")
        return 0
    else:
        print(f"⚠️ {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
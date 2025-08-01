import React, { useState, useEffect } from 'react';
import { Plus, Wallet, TrendingUp, TrendingDown, IndianRupee, ExternalLink, Smartphone, Zap, MessageSquare, Settings } from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Badge } from './components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Textarea } from './components/ui/textarea';
import { Switch } from './components/ui/switch';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const CATEGORIES = ['Food', 'Transport', 'Bills', 'Shopping', 'Income'];

const PAYMENT_SERVICES = {
  swiggy: {
    name: 'Swiggy',
    url: 'https://www.swiggy.com',
    color: '#fc8019',
    icon: '🍔'
  },
  zomato: {
    name: 'Zomato',
    url: 'https://www.zomato.com',
    color: '#e23744',
    icon: '🍕'
  },
  gpay: {
    name: 'Google Pay',
    url: 'https://pay.google.com',
    color: '#4285f4',
    icon: '💳'
  }
};

function App() {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({
    total_income: 0,
    total_expenses: 0,
    balance: 0,
    category_breakdown: {}
  });
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isSMSDialogOpen, setIsSMSDialogOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    category: '',
    type: 'expense'
  });
  const [smsData, setSmsData] = useState({
    message: '',
    sender: ''
  });
  const [autoSync, setAutoSync] = useState(false);
  const [loading, setLoading] = useState(false);
  const [smsLoading, setSmsLoading] = useState(false);

  // Fetch transactions
  const fetchTransactions = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/transactions`);
      const data = await response.json();
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  // Fetch summary
  const fetchSummary = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/summary`);
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  // Parse SMS for transaction
  const parseSMS = async (e) => {
    e.preventDefault();
    setSmsLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/parse-sms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(smsData),
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('Transaction created successfully from SMS!');
        setSmsData({ message: '', sender: '' });
        setIsSMSDialogOpen(false);
        fetchTransactions();
        fetchSummary();
      } else {
        alert('Could not parse transaction from SMS. Please check the message format.');
      }
    } catch (error) {
      console.error('Error parsing SMS:', error);
      alert('Error parsing SMS. Please try again.');
    } finally {
      setSmsLoading(false);
    }
  };

  // Handle payment service redirect
  const handlePaymentServiceRedirect = (service) => {
    const serviceConfig = PAYMENT_SERVICES[service];
    if (serviceConfig) {
      window.open(serviceConfig.url, '_blank');
    }
  };

  // Sync payments (placeholder)
  const syncPayments = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/sync-payments`, {
        method: 'POST',
      });
      const result = await response.json();
      alert(result.message);
    } catch (error) {
      console.error('Error syncing payments:', error);
      alert('Error syncing payments. Please try again.');
    }
  };

  // Add transaction
  const addTransaction = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Validate required fields
    if (!formData.amount || !formData.description || !formData.category) {
      alert('Please fill in all required fields');
      setLoading(false);
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/transactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          amount: parseFloat(formData.amount)
        }),
      });
      
      if (response.ok) {
        setFormData({
          amount: '',
          description: '',
          date: new Date().toISOString().split('T')[0],
          category: '',
          type: 'expense'
        });
        setIsDialogOpen(false);
        fetchTransactions();
        fetchSummary();
      } else {
        const errorData = await response.json();
        alert('Error creating transaction: ' + (errorData.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error adding transaction:', error);
      alert('Error adding transaction. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Delete transaction
  const deleteTransaction = async (id) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/transactions/${id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        fetchTransactions();
        fetchSummary();
      }
    } catch (error) {
      console.error('Error deleting transaction:', error);
    }
  };

  useEffect(() => {
    fetchTransactions();
    fetchSummary();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-800 mb-2">Finance Tracker</h1>
            <p className="text-slate-600">Track your income and expenses effortlessly</p>
          </div>
          <div className="flex gap-3 mt-4 md:mt-0">
            <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Settings
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>App Settings</DialogTitle>
                  <DialogDescription>
                    Configure your finance tracker preferences.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="text-base">Auto-sync Payments</Label>
                      <p className="text-sm text-muted-foreground">
                        Automatically sync payments from connected services
                      </p>
                    </div>
                    <Switch
                      checked={autoSync}
                      onCheckedChange={setAutoSync}
                    />
                  </div>
                  <Button onClick={syncPayments} className="w-full">
                    <Zap className="w-4 h-4 mr-2" />
                    Sync Now
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            
            <Dialog open={isSMSDialogOpen} onOpenChange={setIsSMSDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Import SMS
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Import from SMS</DialogTitle>
                  <DialogDescription>
                    Paste your bank SMS to automatically create a transaction.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={parseSMS} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="sender">Sender (Optional)</Label>
                    <Input
                      id="sender"
                      placeholder="e.g., SBI, HDFC, ICICI"
                      value={smsData.sender}
                      onChange={(e) => setSmsData({...smsData, sender: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="sms-message">SMS Message *</Label>
                    <Textarea
                      id="sms-message"
                      placeholder="Paste your bank SMS here..."
                      value={smsData.message}
                      onChange={(e) => setSmsData({...smsData, message: e.target.value})}
                      required
                      rows={4}
                    />
                  </div>
                  <Button type="submit" disabled={smsLoading} className="w-full">
                    {smsLoading ? 'Parsing...' : 'Parse SMS'}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
            
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700">
                  <Plus className="w-4 h-4" />
                  Add Transaction
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Add New Transaction</DialogTitle>
                  <DialogDescription>
                    Enter your transaction details below.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={addTransaction} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="amount">Amount (₹)</Label>
                      <Input
                        id="amount"
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={formData.amount}
                        onChange={(e) => setFormData({...formData, amount: e.target.value})}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="date">Date</Label>
                      <Input
                        id="date"
                        type="date"
                        value={formData.date}
                        onChange={(e) => setFormData({...formData, date: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="category">Category *</Label>
                    <Select 
                      onValueChange={(value) => {
                        console.log('Category selected:', value);
                        setFormData({...formData, category: value});
                      }} 
                      value={formData.category}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {CATEGORIES.map((category) => (
                          <SelectItem key={category} value={category}>
                            {category}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="type">Type</Label>
                    <Select onValueChange={(value) => setFormData({...formData, type: value})} defaultValue="expense">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="expense">Expense</SelectItem>
                        <SelectItem value="income">Income</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      placeholder="Enter transaction details..."
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      required
                    />
                  </div>
                  
                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? 'Adding...' : 'Add Transaction'}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Quick Actions */}
        <Card className="bg-white shadow-lg border-0 mb-8">
          <CardHeader>
            <CardTitle className="text-xl text-slate-800 flex items-center gap-2">
              <Smartphone className="w-5 h-5" />
              Quick Actions
            </CardTitle>
            <CardDescription>Access your favorite payment services</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(PAYMENT_SERVICES).map(([key, service]) => (
                <Button
                  key={key}
                  onClick={() => handlePaymentServiceRedirect(key)}
                  variant="outline"
                  className="flex items-center gap-3 p-6 h-auto hover:shadow-md transition-all"
                  style={{ borderColor: service.color }}
                >
                  <span className="text-2xl">{service.icon}</span>
                  <div className="text-left">
                    <div className="font-semibold" style={{ color: service.color }}>
                      {service.name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Open {service.name}
                    </div>
                  </div>
                  <ExternalLink className="w-4 h-4 ml-auto" />
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="bg-white shadow-lg border-0 hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total Income</CardTitle>
              <TrendingUp className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-700 flex items-center">
                <IndianRupee className="w-5 h-5 mr-1" />
                {summary.total_income.toLocaleString('en-IN')}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white shadow-lg border-0 hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total Expenses</CardTitle>
              <TrendingDown className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-700 flex items-center">
                <IndianRupee className="w-5 h-5 mr-1" />
                {summary.total_expenses.toLocaleString('en-IN')}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white shadow-lg border-0 hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Balance</CardTitle>
              <Wallet className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold flex items-center ${summary.balance >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                <IndianRupee className="w-5 h-5 mr-1" />
                {summary.balance.toLocaleString('en-IN')}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Transactions */}
        <Card className="bg-white shadow-lg border-0">
          <CardHeader>
            <CardTitle className="text-xl text-slate-800">Recent Transactions</CardTitle>
            <CardDescription>Your latest financial activities</CardDescription>
          </CardHeader>
          <CardContent>
            {transactions.length === 0 ? (
              <div className="text-center py-12">
                <Wallet className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-500 text-lg">No transactions yet</p>
                <p className="text-slate-400">Add your first transaction to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {transactions.slice(0, 10).map((transaction) => (
                  <div key={transaction.id} className="flex items-center justify-between p-4 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-full ${transaction.type === 'income' ? 'bg-emerald-100' : 'bg-red-100'}`}>
                        {transaction.type === 'income' ? 
                          <TrendingUp className="w-4 h-4 text-emerald-600" /> : 
                          <TrendingDown className="w-4 h-4 text-red-600" />
                        }
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{transaction.description}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="secondary" className="text-xs">
                            {transaction.category}
                          </Badge>
                          <span className="text-sm text-slate-500">{transaction.date}</span>
                          {transaction.source === 'sms' && (
                            <Badge variant="outline" className="text-xs">
                              SMS
                            </Badge>
                          )}
                          {transaction.webhook_data && (
                            <Badge variant="outline" className="text-xs">
                              {transaction.webhook_data.service}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`font-semibold flex items-center ${transaction.type === 'income' ? 'text-emerald-700' : 'text-red-700'}`}>
                        <IndianRupee className="w-4 h-4 mr-1" />
                        {transaction.amount.toLocaleString('en-IN')}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteTransaction(transaction.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;
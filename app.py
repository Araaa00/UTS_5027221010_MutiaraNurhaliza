from flask import Flask, render_template, request, redirect, url_for, session
import grpc
import financial_tracking_pb2
import financial_tracking_pb2_grpc

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ganti dengan kunci rahasia yang lebih aman
channel = grpc.insecure_channel('localhost:50051')
stub = financial_tracking_pb2_grpc.FinancialTrackerStub(channel)

@app.route('/')
def index():
    if 'username' in session and session['role'] == 'admin':
        # Mengambil semua transaksi
        transactions = []
        response = stub.ReadAllTransactions(financial_tracking_pb2.Empty())
        for transaction in response:
            transactions.append({
                'id': transaction.id,
                'description': transaction.description,
                'amount': transaction.amount
            })
        return render_template('index.html', transactions=transactions)
    else:
        return redirect(url_for('login'))

# Route untuk login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        response = stub.Login(financial_tracking_pb2.User(username=username, password=password))
        if response.username:
            session['username'] = response.username
            session['role'] = response.role  # Menyimpan role pengguna dalam sesi
            if response.role == 'admin':
                return redirect(url_for('index'))  # Redirect ke halaman admin jika role adalah 'admin'
            elif response.role == 'user':
                return redirect(url_for('add_transaction'))  # Redirect ke halaman tambah transaksi jika role adalah 'user'
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

# Route untuk logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Route untuk registrasi (sign up)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = stub.SignUp(financial_tracking_pb2.User(username=username, password=password))
        if response.username:
            session['username'] = response.username
            return redirect(url_for('index'))
        else:
            return render_template('signup.html', error="Username already exists")
    return render_template('signup.html')

# Route untuk menambahkan transaksi
@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if 'username' in session:
        if request.method == 'POST':
            id = request.form['id']
            description = request.form['description']
            amount = float(request.form['amount'])

            transaction = financial_tracking_pb2.Transaction(
                id=id, description=description, amount=amount)
            response = stub.AddTransaction(transaction)
            return redirect(url_for('add_transaction'))
        return render_template('add_transaction.html')
    else:
        return redirect(url_for('login'))

# Route untuk membaca detail transaksi
@app.route('/read_transaction', methods=['GET', 'POST'])
def read_transaction():
    if 'username' in session:
        if request.method == 'POST':
            transaction_id = request.form['transaction_id']
            response = stub.ReadTransaction(financial_tracking_pb2.TransactionId(id=transaction_id))
            if response.id:
                return render_template('transaction_details.html', transaction=response)
            else:
                return render_template('transaction_not_found.html')
        return render_template('read_transaction.html')
    else:
        return redirect(url_for('login'))

# Route untuk mengubah transaksi
@app.route('/update_transaction', methods=['GET', 'POST'])
def update_transaction():
    if 'username' in session:
        if request.method == 'POST':
            transaction_id = request.form['transaction_id']
            description = request.form['description']
            amount = float(request.form['amount'])
            response = stub.UpdateTransaction(financial_tracking_pb2.Transaction(
                id=transaction_id, description=description, amount=amount))
            return redirect(url_for('update_transaction'))
        return render_template('update_transaction.html')
    else:
        return redirect(url_for('login'))

# Route untuk menghapus transaksi
@app.route('/delete_transaction', methods=['GET', 'POST'])
def delete_transaction():
    if 'username' in session:
        if request.method == 'POST':
            transaction_id = request.form['transaction_id']
            response = stub.DeleteTransaction(financial_tracking_pb2.TransactionId(id=transaction_id))
            return redirect(url_for('delete_transaction'))
        return render_template('delete_transaction.html')
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

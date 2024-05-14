import grpc
from concurrent import futures
import financial_tracking_pb2
import financial_tracking_pb2_grpc
import mysql.connector
import hashlib

class FinancialTrackerServicer(financial_tracking_pb2_grpc.FinancialTrackerServicer):
    def __init__(self):
        self.db_connection = mysql.connector.connect(
            host="localhost",
            user="tes",
            password="tes",
            database="test"
        )
        self.cursor = self.db_connection.cursor()

    def SignUp(self, request, context):
        username = request.username
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        
        # Periksa apakah pengguna sudah terdaftar
        sql_check_user = "SELECT * FROM users WHERE username = %s"
        self.cursor.execute(sql_check_user, (username,))
        existing_user = self.cursor.fetchone()
        if existing_user:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("User already exists")
            return financial_tracking_pb2.User()
        
        # Tambahkan pengguna baru ke database
        sql_add_user = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
        values = (username, password_hash)
        self.cursor.execute(sql_add_user, values)
        self.db_connection.commit()
        
        return financial_tracking_pb2.User(username=username)

    def Login(self, request, context):
        username = request.username
        password_hash = hashlib.sha256(request.password.encode()).hexdigest()
        
        # Periksa apakah pengguna ada dan kata sandi cocok
        sql_check_user = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
        self.cursor.execute(sql_check_user, (username, password_hash))
        user = self.cursor.fetchone()
        if not user:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Invalid username or password")
            return financial_tracking_pb2.User()
        
        # Ambil peran pengguna dari database
        sql_get_role = "SELECT role FROM users WHERE username = %s"
        self.cursor.execute(sql_get_role, (username,))
        role = self.cursor.fetchone()[0]  # Mengambil nilai peran dari tuple pertama kolom 'role'
        
        return financial_tracking_pb2.User(username=username, role=role)

    def AddTransaction(self, request, context):
        sql = "INSERT INTO transactions (transaction_id, description, amount) VALUES (%s, %s, %s)"
        values = (request.id, request.description, request.amount)
        self.cursor.execute(sql, values)
        self.db_connection.commit()
        return request

    def GetTransactions(self, request_iterator, context):
        sql = "SELECT transaction_id, description, amount FROM transactions"
        self.cursor.execute(sql)
        for row in self.cursor.fetchall():
            yield financial_tracking_pb2.Transaction(
                id=row[0], description=row[1], amount=row[2])

    def ReadTransaction(self, request, context):
        sql = "SELECT transaction_id, description, amount FROM transactions WHERE transaction_id = %s"
        self.cursor.execute(sql, (request.id,))
        result = self.cursor.fetchone()
        if result:
            return financial_tracking_pb2.Transaction(
                id=result[0], description=result[1], amount=result[2])
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Transaction not found")
            return financial_tracking_pb2.Transaction()

    def UpdateTransaction(self, request, context):
        sql = "UPDATE transactions SET description = %s, amount = %s WHERE transaction_id = %s"
        values = (request.description, request.amount, request.id)
        self.cursor.execute(sql, values)
        self.db_connection.commit()
        return request

    def DeleteTransaction(self, request, context):
        sql = "DELETE FROM transactions WHERE transaction_id = %s"
        self.cursor.execute(sql, (request.id,))
        self.db_connection.commit()
        return financial_tracking_pb2.Transaction(id=request.id)

    def ReadAllTransactions(self, request, context):
        sql = "SELECT transaction_id, description, amount FROM transactions"
        self.cursor.execute(sql)
        for result in self.cursor.fetchall():
            yield financial_tracking_pb2.Transaction(
                id=result[0], description=result[1], amount=result[2])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    financial_tracking_pb2_grpc.add_FinancialTrackerServicer_to_server(
        FinancialTrackerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started. Listening on port 50051.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

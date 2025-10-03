import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
import django

django.setup()

from alx_backend_graphql_crm.schema import schema

def run(label, query, variables=None):
		res = schema.execute(query, variable_values=variables)
		print(f"\n== {label} ==")
		print('errors:', res.errors)
		print('data:', res.data)
		return res

# Hello
run('hello', '{ hello }')

# Ensure lists resolve
run('allCustomers', 'query{ allCustomers{ edges{ node{ id email createdAt } } } }')

# Create customer
run('createCustomer', '''
mutation($input: CreateCustomerInput!){
	createCustomer(input: $input){
		success
		message
		customer{ id name email phone }
		errors
	}
}
''', {"input": {"name": "Alice", "email": "alice@example.com", "phone": "+1234567890"}})

# Bulk create customers
run('bulkCreateCustomers', '''
mutation($input: [CustomerInput!]!){
	bulkCreateCustomers(input: $input){
		success
		message
		customers{ id name email }
		errors
	}
}
''', {"input": [
		{"name": "Bob", "email": "bob@example.com", "phone": "123-456-7890"},
		{"name": "Carol", "email": "carol@example.com"}
]})

# Create products
run('createProduct1', '''
mutation($input: CreateProductInput!){
	createProduct(input: $input){ product{ id name price stock } errors success }
}
''', {"input": {"name": "Laptop", "price": 999.99, "stock": 10}})

run('createProduct2', '''
mutation($input: CreateProductInput!){
	createProduct(input: $input){ product{ id name price stock } errors success }
}
''', {"input": {"name": "Mouse", "price": 25.5, "stock": 100}})

# Create order
run('createOrder', '''
mutation($input: CreateOrderInput!){
	createOrder(input: $input){
		success
		message
		order{ id totalAmount orderDate customer{ name } products{ name price } product{ name } }
		errors
	}
}
''', {"input": {"customerId": "1", "productIds": ["1","2"]}})

# Filter queries
run('filterCustomers', 'query{ allCustomers(filter: { nameIcontains: "Ali", createdAtGte: "2020-01-01" }){ edges{ node{ id name email createdAt } } } }')
run('filterProducts', 'query{ allProducts(filter: { priceGte: 20, priceLte: 1000 }, orderBy: "-stock"){ edges{ node{ id name price stock } } } }')
run('filterOrders', 'query{ allOrders(filter: { customerName: "Alice", totalAmountGte: 20 }){ edges{ node{ id totalAmount orderDate customer{ name } product{ name } } } } }')

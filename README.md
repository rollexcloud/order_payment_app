# Order & Payment Web Application

A production-ready Python web application for taking customer orders with **FREE UPI payment integration** using QR codes and UPI deep linking.

## 🚀 **Quick Deploy - Recommended: Render.com**

**Deploy in 5 minutes for free:**
1. Push code to GitHub
2. Create account at [render.com](https://render.com)
3. New Web Service → Connect GitHub repo
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn app:app --workers 4 --bind 0.0.0.0:$PORT`
6. Add environment variables (see DEPLOYMENT.md)
7. Deploy! 🎉

**Detailed deployment guide:** See [DEPLOYMENT.md](DEPLOYMENT.md)

## Features

- **Product Selection**: Browse and select products with quantity control
- **Customer Management**: Collect customer details (minimal data collection)
- **FREE UPI Payments**: No transaction fees - direct UPI integration via QR codes and deep linking
- **Mobile UPI App Integration**: Opens UPI apps directly on mobile devices
- **QR Code Generation**: Automatic QR code generation for easy scanning
- **Order Management**: Track orders with status updates (pending, paid, failed)
- **Admin Dashboard**: View and manage all orders with reporting
- **Product Management**: Add, edit, delete products dynamically
- **Admin Security**: Secure login system with session management
- **CSV Reports**: Download order reports by date range
- **Responsive Design**: Mobile-friendly interface
- **Production Ready**: Security headers, logging, error handling
- **Database**: SQLite for development, PostgreSQL for production

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (dev) / PostgreSQL (production) with SQLAlchemy ORM
- **Authentication**: Flask-Login for secure admin access
- **Payment**: FREE UPI QR codes and deep linking (no transaction fees)
- **Frontend**: HTML, CSS, JavaScript
- **QR Generation**: qrcode library
- **Deployment**: Gunicorn (production server)
- **Security**: Werkzeug password hashing, session management

## Prerequisites

- Python 3.8 or higher
- UPI ID (any UPI ID - PhonePe, Paytm, Google Pay, etc.)
- Git (optional)

## Installation

### Local Development

1. **Clone or download the project**
   ```bash
   cd order_payment_app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/MacOS:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your UPI details:
   ```
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///orders.db
   UPI_ID=yourupi@upi  # Your UPI ID (e.g., mobile@upi)
   PAYEE_NAME=Your Business Name  # Your business name
   FLASK_ENV=development
   ```

5. **Get your UPI ID**
   - Any UPI ID works (PhonePe, Paytm, Google Pay, etc.)
   - Format: `mobile@upi` or `name@ybl` or similar
   - No account signup required for payment gateway

### Production Deployment

**Important**: Before deploying, review the [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for critical changes required.

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions.

**Quick Deploy (Render.com):**
1. Push code to GitHub
2. Create account at [render.com](https://render.com)
3. New Web Service → Connect GitHub repo
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn app:app --workers 4 --bind 0.0.0.0:$PORT`
6. Add environment variables (SECRET_KEY, UPI_ID, PAYEE_NAME, FLASK_ENV=production)
7. Deploy!

## Running the Application

### Development Mode
```bash
python app.py
```
The application will be available at `http://localhost:5000`

### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Usage

1. **Place an Order**
   - Visit the homepage
   - Select products and quantities
   - Fill in customer details
   - Click "Place Order & Pay"

2. **Payment Process**
   - UPI QR code will be displayed
   - **On Mobile**: Click "Open UPI App" to pay directly
   - **On Desktop**: Scan QR code with any UPI app
   - After payment, enter transaction details and confirm
   - Receive order confirmation

3. **View Orders**
   - Admin dashboard: `/admin/orders`
   - Individual order details: `/order/<order_id>`

## Project Structure

```
order_payment_app/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── templates/                 # HTML templates
│   ├── index.html            # Main order page
│   ├── order_details.html    # Order details page
│   └── admin_orders.html     # Admin dashboard
└── static/                   # Static assets
    ├── css/
    │   └── style.css         # Main stylesheet
    └── js/
        └── app.js            # Frontend JavaScript
```

## API Endpoints

- `GET /` - Main order page
- `POST /create_order` - Create new order and generate UPI QR code
- `POST /confirm_payment` - Confirm payment manually (after UPI payment)
- `GET /order/<order_id>` - View order details
- `GET /admin/orders` - Admin dashboard

## Security Features

- Environment variable configuration
- SQL injection prevention (SQLAlchemy ORM)
- Input validation
- Manual payment confirmation for security
- CSRF protection (Flask-WTF can be added for enhanced security)

## Customization

### Adding Products
Edit the `MENU_ITEMS` list in `app.py`:
```python
MENU_ITEMS = [
    {'id': 1, 'name': 'Product Name', 'price': 500, 'description': 'Description'},
    # Add more products...
]
```

### Configuring UPI ID
Edit your `.env` file with your UPI ID:
```
UPI_ID=yourmobile@upi
PAYEE_NAME=Your Business Name
```

### Database
For production, consider using PostgreSQL or MySQL:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/dbname'
```

## Deployment

### Using Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Systemd (Linux)
Create `/etc/systemd/system/order_app.service`:
```ini
[Unit]
Description=Order Payment App
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/order_payment_app
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

### Using Docker (Optional)
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Troubleshooting

**QR code not generating**: Ensure UPI ID is correctly configured in `.env`

**UPI app not opening**: Make sure you're on a mobile device with UPI apps installed

**Database errors**: Delete `orders.db` and restart the app to recreate the database

**Static files not loading**: Check that Flask is running in the correct directory

**Payment confirmation fails**: Ensure order ID is valid and database is accessible

## License

This project is provided as-is for educational and commercial use.

## Support

For UPI-related issues, ensure your UPI ID is correctly configured and test with different UPI apps (PhonePe, Paytm, Google Pay).

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import os
from datetime import datetime
from decimal import Decimal

class PDFService:
    """
    Utility class for generating PDF documents (order receipts, monthly reports) using WeasyPrint.
    """
    @staticmethod
    def generate_order_receipt_pdf(order):
        """
        Generate a beautiful PDF receipt for an order using WeasyPrint.
        Renders an HTML template and applies custom CSS.
        """
        # Prepare context data for the template
        context = {
            'order': order,
            'items': order.items.all().select_related('product', 'size'),
            'company_name': 'YD Bloom',
            'company_address': '123 Fashion Street, Style City, SC 12345',
            'company_phone': '+1 (555) 123-4567',
            'company_email': 'support@backend.com',
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        }
        # Render HTML template
        html_string = render_to_string('admin/pdf/order_receipt.html', context)
        # Create PDF
        font_config = FontConfiguration()
        html = HTML(string=html_string)
        css = CSS(
            string='''
                @page {
                    size: A4;
                    margin: 1cm;
                    @top-center {
                        content: "YD Bloom - Order Receipt";
                        font-size: 10pt;
                        color: #666;
                    }
                    @bottom-center {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 10pt;
                        color: #666;
                    }
                }
                body {
                    font-family: Arial, sans-serif;
                    font-size: 12pt;
                    line-height: 1.4;
                    color: #333;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #4c51bf;
                    padding-bottom: 20px;
                }
                .company-name {
                    font-size: 24pt;
                    font-weight: bold;
                    color: #4c51bf;
                    margin-bottom: 5px;
                }
                .company-details {
                    font-size: 10pt;
                    color: #666;
                }
                .receipt-info {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                }
                .order-details, .customer-details {
                    flex: 1;
                }
                .section-title {
                    font-size: 14pt;
                    font-weight: bold;
                    color: #4c51bf;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 5px;
                }
                .items-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                .items-table th {
                    background-color: #f8f9fa;
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                }
                .items-table td {
                    border: 1px solid #ddd;
                    padding: 10px;
                }
                .total-section {
                    text-align: right;
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 2px solid #4c51bf;
                }
                .total-amount {
                    font-size: 16pt;
                    font-weight: bold;
                    color: #4c51bf;
                }
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    font-size: 10pt;
                    color: #666;
                    border-top: 1px solid #ddd;
                    padding-top: 20px;
                }
                .status-badge {
                    display: inline-block;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 10pt;
                    font-weight: bold;
                    text-transform: uppercase;
                }
                .status-pending { background-color: #fff3cd; color: #856404; }
                .status-paid { background-color: #d4edda; color: #155724; }
                .status-shipped { background-color: #cce5ff; color: #004085; }
                .status-delivered { background-color: #d1ecf1; color: #0c5460; }
                .status-cancelled { background-color: #f8d7da; color: #721c24; }
            ''',
            font_config=font_config
        )
        # Generate PDF
        pdf = html.write_pdf(stylesheets=[css], font_config=font_config)
        return pdf

    @staticmethod
    def get_order_receipt_response(order):
        """
        Return an HTTP response with the PDF receipt for download.
        """
        pdf_content = PDFService.generate_order_receipt_pdf(order)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_order_{order.id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        return response

    @staticmethod
    def generate_monthly_revenue_report_pdf(month, year):
        """
        Generate a PDF report for monthly revenue using WeasyPrint.
        Includes order summary and totals for the month.
        """
        from django.db.models import Sum, Count
        from django.utils import timezone
        from .models import Order
        # Get orders for the specified month
        start_date = timezone.datetime(year, month, 1)
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1)
        else:
            end_date = timezone.datetime(year, month + 1, 1)
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            status__in=['paid', 'shipped', 'delivered']
        )
        total_revenue = orders.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        total_orders = orders.count()
        context = {
            'month': start_date.strftime('%B %Y'),
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'orders': orders.select_related('user').prefetch_related('items__product'),
            'company_name': 'YD Bloom',
            'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
        }
        # Render HTML template
        html_string = render_to_string('admin/pdf/monthly_report.html', context)
        font_config = FontConfiguration()
        html = HTML(string=html_string)
        css = CSS(
            string='''
                @page {
                    size: A4;
                    margin: 1cm;
                    @top-center {
                        content: "YD Bloom - Monthly Revenue Report";
                        font-size: 10pt;
                        color: #666;
                    }
                    @bottom-center {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 10pt;
                        color: #666;
                    }
                }
                body {
                    font-family: Arial, sans-serif;
                    font-size: 12pt;
                    line-height: 1.4;
                    color: #333;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #4c51bf;
                    padding-bottom: 20px;
                }
                .company-name {
                    font-size: 24pt;
                    font-weight: bold;
                    color: #4c51bf;
                    margin-bottom: 5px;
                }
                .report-title {
                    font-size: 18pt;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }
                .summary-section {
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 30px;
                }
                .summary-item {
                    display: inline-block;
                    margin-right: 40px;
                }
                .summary-label {
                    font-size: 10pt;
                    color: #666;
                    text-transform: uppercase;
                }
                .summary-value {
                    font-size: 16pt;
                    font-weight: bold;
                    color: #4c51bf;
                }
                .orders-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                .orders-table th, .orders-table td {
                    border: 1px solid #ddd;
                    padding: 10px;
                }
                .orders-table th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
            ''',
            font_config=font_config
        )
        # Generate PDF
        pdf = html.write_pdf(stylesheets=[css], font_config=font_config)
        return pdf

    @staticmethod
    def get_monthly_revenue_response(month, year):
        """
        Return an HTTP response with the monthly revenue PDF report for download.
        """
        pdf_content = PDFService.generate_monthly_revenue_report_pdf(month, year)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="monthly_report_{month}_{year}.pdf"'
        return response 
# Copyright (c) 2024, abdopcnet@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# Define columns
columns = [
    {
        "fieldname": "reference_name",
        "label": _("رقم الفاتورة"),
        "fieldtype": "Link",
        "options": "Sales Invoice",
        "width": 200
    },
    {
        "fieldname": "custom_sales_invoice_number",
        "label": _("رقم الفاتورة المخصص"),
        "fieldtype": "Data",
        "width": 200
    },
    {
        "fieldname": "customer_name",
        "label": _("اسم العميل"),
        "fieldtype": "Link",
        "options": "Customer",
        "width": 200
    },
    {
        "fieldname": "sales_persons",
        "label": _("مندوب المبيعات"),
        "fieldtype": "Data",
        "width": 200
    },
    {
        "fieldname": "total_paid_amount",
        "label": _("إجمالي المدفوع"),
        "fieldtype": "Currency",
        "width": 150
    },
    {
        "fieldname": "base_total_taxes_and_charges",
        "label": _("إجمالي الضرائب"),
        "fieldtype": "Currency",
        "width": 200
    },
    {
        "fieldname": "amount_applicable_for_commission",
        "label": _("المبلغ القابل للعمولة"),
        "fieldtype": "Currency",
        "width": 200
    },
    {
        "fieldname": "commission_rates",
        "label": _("نسب العمولة"),
        "fieldtype": "Data",
        "width": 120
    },
    {
        "fieldname": "total_commission_amount",
        "label": _("إجمالي العمولة"),
        "fieldtype": "Currency",
        "width": 200
    }
]

# Fetch data
def execute(filters=None):
    # Extract filters
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    customer_name = filters.get("customer_name")
    
    # Build SQL query
    query = """
        SELECT
            `tabPayment Entry Reference`.reference_name,
            `tabSales Invoice`.custom_sales_invoice_number,
            SUM(`tabPayment Entry Reference`.total_paid_amount) AS total_paid_amount,
            (SELECT GROUP_CONCAT(DISTINCT `tabSales Team`.sales_person SEPARATOR ', ')
             FROM `tabSales Team`
             WHERE `tabSales Team`.parent = `tabPayment Entry Reference`.reference_name) AS sales_persons,
            (SELECT GROUP_CONCAT(DISTINCT `tabSales Team`.commission_rate SEPARATOR ', ')
             FROM `tabSales Team`
             WHERE `tabSales Team`.parent = `tabPayment Entry Reference`.reference_name) AS commission_rates,
            SUM(`tabPayment Entry Reference`.total_paid_amount) - `tabSales Invoice`.base_total_taxes_and_charges AS amount_applicable_for_commission,
            (SUM(`tabPayment Entry Reference`.total_paid_amount) - `tabSales Invoice`.base_total_taxes_and_charges) * (SELECT AVG(`tabSales Team`.commission_rate) / 100
                                     FROM `tabSales Team`
                                     WHERE `tabSales Team`.parent = `tabPayment Entry Reference`.reference_name) AS total_commission_amount,
            `tabSales Invoice`.base_total_taxes_and_charges AS base_total_taxes_and_charges,
            `tabSales Invoice`.customer_name AS customer_name
        FROM
            (SELECT
                 `tabPayment Entry Reference`.reference_name,
                 `tabPayment Entry Reference`.parent,
                 SUM(DISTINCT `tabPayment Entry`.paid_amount) AS total_paid_amount
             FROM
                 `tabPayment Entry Reference`
             INNER JOIN
                 `tabPayment Entry` ON `tabPayment Entry`.name = `tabPayment Entry Reference`.parent
             WHERE
                 `tabPayment Entry Reference`.reference_doctype = 'Sales Invoice'
             GROUP BY
                 `tabPayment Entry Reference`.reference_name, `tabPayment Entry Reference`.parent) AS `tabPayment Entry Reference`
        INNER JOIN
            `tabSales Invoice` ON `tabSales Invoice`.name = `tabPayment Entry Reference`.reference_name
        WHERE
            `tabSales Invoice`.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """

    # Add customer name filter if provided
    if customer_name:
        query += " AND `tabSales Invoice`.customer_name = %(customer_name)s"
        
    query += """
        GROUP BY
            `tabPayment Entry Reference`.reference_name,
            `tabSales Invoice`.base_total_taxes_and_charges,
            `tabSales Invoice`.customer_name,
            `tabSales Invoice`.custom_sales_invoice_number
    """

    # Set parameters
    params = {
        "from_date": from_date,
        "to_date": to_date
    }
    if customer_name:
        params["customer_name"] = customer_name

    # Execute the query
    data = frappe.db.sql(query, params, as_dict=True)

    return columns, data

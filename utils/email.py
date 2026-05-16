"""
Email sending utility for Alanaatii Backend.
Emails are sent asynchronously using background threads to prevent API delays.
"""
import logging
import threading
import resend
from django.conf import settings

logger = logging.getLogger('apps')

# Configure Resend
resend.api_key = settings.RESEND_API_KEY

def get_frontend_url():
    """Fetches the frontend URL from SiteSettings or defaults to settings."""
    from apps.admin_ops.models import SiteSettings
    try:
        url = SiteSettings.get().frontend_url
    except Exception:
        url = settings.FRONTEND_URL
    return url.rstrip('/')


def send_email(to: str, subject: str, text_body: str, html_body: str = None, attachments: list = None):
    """
    Send a single email in the background via Resend API.
    """
    thread = threading.Thread(
        target=_send_email_sync,
        args=(to, subject, text_body, html_body, attachments)
    )
    thread.start()


def _send_email_sync(to: str, subject: str, text_body: str, html_body: str = None, attachments: list = None):
    """
    Synchronous email sending via Resend SDK.
    """
    try:
        params = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": to,
            "subject": subject,
            "text": text_body,
        }
        if html_body:
            params["html"] = html_body
        if attachments:
            params["attachments"] = attachments
            
        r = resend.Emails.send(params)
        logger.info(f'Email sent via Resend to {to}: {subject} | ID: {r.get("id")}')
    except Exception as e:
        # Log full error for debugging
        logger.error(f'Resend API Error for {to}: {str(e)}')
        print(f'❌ Resend Error: {str(e)}')


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_product_summary(order):
    """Generates a text summary of the product configuration."""
    summary = []
    if order.product_type == 'letterPaper':
        if order.paper:
            summary.append(f"Paper Selection: {order.paper.title}")
        summary.append(f"Sheet Quantity: {order.paper_quantity}")
    else:
        if order.letter_theme:
            summary.append(f"Letter Theme: {order.letter_theme.title}")
        if order.text_style:
            summary.append(f"Calligraphy Style: {order.text_style.title}")
        if order.box:
            summary.append(f"Luxury Box: {order.box.title}")
        if order.gift:
            summary.append(f"Gift Add-on: {order.gift.title}")
    
    if not summary:
        return "Standard Configuration"
    return "\n".join([f"• {item}" for item in summary])


# ─── Customer Emails ──────────────────────────────────────────────────────────

def send_order_placed_email(order):
    """Notify customer that their order was received and payment is pending verification."""
    product_details = _get_product_summary(order)
    subject = f'Order Received – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Thank you for placing your order with Alanaatii!\n\n'
        f'Your Order Details:\n'
        f'-------------------\n'
        f'Order ID: {order.id}\n'
        f'Product: {order.get_product_type_display()}\n'
        f'{product_details}\n'
        f'Total Amount: ₹{order.total_amount}\n\n'
        f'Our admin team will verify your payment and update you shortly.\n'
        f'You can track your order at: {get_frontend_url()}/dashboard/orders/{order.id}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_payment_verified_email(order):
    """Notify customer that payment is verified."""
    product_details = _get_product_summary(order)
    
    if order.product_type == 'letterPaper':
        subject = f'Order Placed Successfully – #{order.id} | Alanaatii'
        action_text = (
            f'We will notify you once your order is out of delivery.\n\n'
            f'We would love to hear your experience with Alanaatii so far:\n'
            f'{get_frontend_url()}/submit-review?order={order.id}'
        )
    else:
        subject = f'Order Placed Successfully – #{order.id} | Alanaatii'
        # Dynamic body based on whether details are needed
        if order.status == 'awaiting_details':
            action_text = (
                f'Next Step: Please fill in the required details for your letter so our writer can begin crafting it.\n\n'
                f'Fill Details Here: {get_frontend_url()}/dashboard/details/{order.id}'
            )
        else:
            action_text = (
                f'Next Step: Our professional artists will now begin processing your order. '
                f'We will notify you once your creation is ready.'
            )

    body = (
        f'Hi {order.customer_name},\n\n'
        f'Great news! Your payment for Order #{order.id} has been verified.\n\n'
        f'Order Summary:\n'
        f'{product_details}\n\n'
        f'{action_text}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_payment_rejected_email(order, reason: str):
    """Notify customer that payment screenshot was rejected."""
    subject = f'Payment Not Verified – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Unfortunately, we could not verify your payment for Order #{order.id}.\n\n'
        f'Reason: {reason}\n\n'
        f'Please upload a valid payment screenshot here:\n'
        f'{get_frontend_url()}/dashboard/orders/{order.id}\n\n'
        f'If you need help, contact us at {settings.DEFAULT_FROM_EMAIL}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_details_reminder_email(order, secure_link_url: str = None):
    """Remind customer to fill in the relationship questionnaire."""
    subject = f'Action Required: Fill Order Details – #{order.id} | Alanaatii'
    link = secure_link_url or f'{get_frontend_url()}/dashboard/details/{order.id}'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Your order #{order.id} is waiting for your story!\n\n'
        f'Our writer is ready to begin, but we need a few more details from you to craft the perfect letter.\n\n'
        f'Click here to fill in the details:\n{link}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_script_ready_email(order, secure_link_url: str = None):
    """Notify customer that their script is ready for review."""
    subject = f'Your Letter Script is Ready! – #{order.id} | Alanaatii'
    link = secure_link_url or f'{get_frontend_url()}/dashboard/scripts?order={order.id}'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Exciting news! Our writer has completed the script for your letter (Order #{order.id}).\n\n'
        f'Please review it and let us know:\n'
        f'• Approve it — and we will begin writing the physical letter\n'
        f'• Request changes — and our writer will revise it\n\n'
        f'Review your script here:\n{link}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_revision_submitted_email(order):
    """Notify customer that writer submitted a revised script."""
    subject = f'Script Revision Ready – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Your writer has submitted the revised script for Order #{order.id}.\n\n'
        f'Review it here:\n{get_frontend_url()}/dashboard/scripts?order={order.id}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_out_for_delivery_email(order):
    """Notify customer their order is out for delivery."""
    subject = f'Your Letter is On Its Way! – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Your luxury letter (Order #{order.id}) has been dispatched!\n\n'
        f'Courier: {order.courier_name or "Our Delivery Partner"}\n'
        f'Tracking ID: {order.tracking_id or "Will be updated shortly"}\n'
        f'Estimated Arrival: {order.est_arrival or "As per schedule"}\n\n'
        f'Track your order: {get_frontend_url()}/dashboard/orders/{order.id}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_delivered_email(order, include_script=False):
    """Notify customer their order is delivered, or auto-deliver digital scripts."""
    subject = f'Delivered with Love – #{order.id} | Alanaatii'
    
    html_body = None
    attachments = None
    
    if include_script and order.script_content:
        # For Script-Only products: beautifully format the script in the email
        # and attach it as a simple text file.
        script_formatted = order.script_content.replace('\n', '<br>')
        
        body = (
            f'Hi {order.customer_name},\n\n'
            f'Your luxury script (Order #{order.id}) is complete and delivered!\n\n'
            f'We have included your full script below, and also attached it as a text file for your convenience.\n\n'
            f'We would love to hear your feedback:\n'
            f'{get_frontend_url()}/submit-review?order={order.id}\n\n'
            f'With love,\nTeam Alanaatii'
        )
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
            <p>Hi <strong>{order.customer_name}</strong>,</p>
            <p>Your luxury script (Order #{order.id}) is complete and delivered!</p>
            <p>We have included your full script below, and also attached it as a text file for your convenience.</p>
            <hr style="border: 1px solid #eee; margin: 30px 0;" />
            <h2 style="color: #6C40B5; text-align: center; font-family: 'Georgia', serif;">Your Script</h2>
            <div style="background-color: #f9f9f9; padding: 25px; border-radius: 8px; font-size: 16px; line-height: 1.6; white-space: pre-wrap; font-family: 'Georgia', serif; border-left: 4px solid #6C40B5;">
{script_formatted}
            </div>
            <hr style="border: 1px solid #eee; margin: 30px 0;" />
            <p style="text-align: center;">
                <a href="{get_frontend_url()}/submit-review?order={order.id}" style="background-color: #6C40B5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Leave a Review</a>
            </p>
            <p style="text-align: center; color: #888; font-size: 14px; margin-top: 30px;">With love,<br>Team Alanaatii</p>
        </div>
        """
        
        attachments = [
            {
                "filename": f"Alanaatii_Script_{order.id}.txt",
                "content": list(order.script_content.encode('utf-8'))
            }
        ]
        
    else:
        body = (
            f'Hi {order.customer_name},\n\n'
            f'Your order #{order.id} has been delivered!\n\n'
            f'We hope your letter brings joy to {order.recipient_name}.\n\n'
            f'We would love to hear your feedback:\n'
            f'{get_frontend_url()}/submit-review?order={order.id}\n\n'
            f'With love,\nTeam Alanaatii'
        )

    send_email(order.customer_email, subject, body, html_body=html_body, attachments=attachments)


# ─── Writer Emails ────────────────────────────────────────────────────────────

def send_writer_assignment_email(writer, order):
    """Notify writer of a new assignment."""
    subject = f'New Assignment – Order #{order.id} | Alanaatii'
    body = (
        f'Hi {writer.full_name},\n\n'
        f'You have been assigned a new script writing task!\n\n'
        f'Order ID: {order.id}\n'
        f'Product Type: {order.product_type}\n'
        f'Delivery Date: {order.delivery_date}\n'
        f'Relation: {order.relation or "Not specified"}\n\n'
        f'Please log in to your writer dashboard to accept or decline:\n'
        f'{get_frontend_url()}/writer/requests\n\n'
        f'Team Alanaatii'
    )
    send_email(writer.email, subject, body)


def send_writer_revision_email(writer, order):
    """Notify writer of a revision request."""
    subject = f'Revision Requested – Order #{order.id} | Alanaatii'
    body = (
        f'Hi {writer.full_name},\n\n'
        f'The customer has requested a revision for Order #{order.id}.\n\n'
        f'Their feedback:\n{order.revision_note or "Please check your dashboard."}\n\n'
        f'Log in to revise: {get_frontend_url()}/writer/revisions\n\n'
        f'Team Alanaatii'
    )
    send_email(writer.email, subject, body)


def send_writer_payout_email(writer, payout):
    """Notify writer of a new payout."""
    subject = f'Payout Processed – ₹{payout.amount} | Alanaatii'
    body = (
        f'Hi {writer.full_name},\n\n'
        f'Your payout of ₹{payout.amount} has been processed!\n\n'
        f'Reference ID: {payout.reference_id or "N/A"}\n'
        f'Period: {payout.period_start} to {payout.period_end}\n\n'
        f'View your payouts: {get_frontend_url()}/writer/profile\n\n'
        f'Team Alanaatii'
    )
    send_email(writer.email, subject, body)


def send_writer_deadline_alert_email(writer, assignment):
    """Notify writer that a submission deadline is approaching (within 24h)."""
    subject = f'ACTION REQUIRED: Script Deadline Approaching – #{assignment.order_id}'
    body = (
        f'Hi {writer.full_name},\n\n'
        f'This is a friendly reminder that your script for Order #{assignment.order_id} is due soon.\n\n'
        f'Due Date: {assignment.submission_due_at.strftime("%Y-%m-%d %H:%M")}\n\n'
        f'Please ensure you submit your final script through the dashboard to avoid any delays:\n'
        f'{get_frontend_url()}/writer\n\n'
        f'Team Alanaatii'
    )
    send_email(writer.email, subject, body)


# ─── Admin Emails ─────────────────────────────────────────────────────────────

def send_admin_sla_alert_email(admin_email: str, writer, order):
    """Notify admin that writer hasn't accepted assignment within 24h SLA."""
    subject = f'SLA ALERT: Assignment Not Accepted – #{order.id}'
    body = (
        f'An assignment for Order #{order.id} has not been accepted within the 24-hour SLA.\n\n'
        f'Assigned Writer: {writer.full_name} ({writer.email})\n'
        f'Order ID: {order.id}\n\n'
        f'Please check the status and re-assign if necessary:\n'
        f'{get_frontend_url()}/admin/orders\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_admin_new_order_email(admin_email: str, order):
    """Notify admin of a new order requiring payment verification."""
    subject = f'New Order Pending Payment Verification – #{order.id}'
    body = (
        f'A new order has been placed and requires payment verification.\n\n'
        f'Order ID: {order.id}\n'
        f'Customer: {order.customer_name} ({order.customer_email})\n'
        f'Product: {order.product_type}\n'
        f'Amount: ₹{order.total_amount}\n\n'
        f'Verify Payment: {get_frontend_url()}/admin/payments\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_admin_assignment_rejected_email(admin_email: str, writer, order, reason: str):
    """Notify admin that writer rejected an assignment."""
    subject = f'Assignment Rejected – Order #{order.id}'
    body = (
        f'Writer {writer.full_name} has declined the assignment for Order #{order.id}.\n\n'
        f'Reason: {reason}\n\n'
        f'Please re-assign: {get_frontend_url()}/admin/orders\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_admin_script_approved_email(admin_email: str, order):
    """Notify admin that customer approved the script."""
    subject = f'Script Approved – Order #{order.id} Ready for Physical Writing'
    body = (
        f'The customer has approved the script for Order #{order.id}.\n\n'
        f'Customer: {order.customer_name}\n'
        f'Recipient: {order.recipient_name}\n\n'
        f'Please move the order to Under Writing status:\n'
        f'{get_frontend_url()}/admin/orders\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_admin_script_auto_delivered_email(admin_email: str, order):
    """Notify admin that a script-only product was auto-delivered."""
    subject = f'Script Auto-Delivered – Order #{order.id} Completed'
    body = (
        f'The customer has approved the script for Order #{order.id}.\n\n'
        f'Because this is a Script-Only product, it has been automatically marked as DELIVERED '
        f'and the final script was emailed to the customer.\n\n'
        f'Customer: {order.customer_name}\n'
        f'Recipient: {order.recipient_name}\n\n'
        f'No further action is required for this order.\n'
        f'View Order: {get_frontend_url()}/admin/orders\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_admin_delayed_submission_email(admin_email: str, order, writer):
    """Notify admin that a writer submitted a script past the 24-hour revision deadline."""
    subject = f'⚠️ Delayed Submission Alert – Writer {writer.full_name}'
    body = (
        f'Writer {writer.full_name} ({writer.email}) has submitted a revised script for Order #{order.id} past the 24-hour deadline.\n\n'
        f'Customer: {order.customer_name}\n'
        f'Delayed Submissions Count for this writer: {writer.delayed_submissions_count}\n\n'
        f'Please review the writer\'s performance in the admin dashboard:\n'
        f'{get_frontend_url()}/admin/writers\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_otp_email(to_email: str, code: str, purpose: str, role: str = 'admin'):
    """Send OTP for password reset or update to Admin or Writer."""
    is_reset = purpose == 'reset_password'
    portal_name = "Admin" if role == 'admin' else "Writer"
    subject = f'Verification Code: {code} | Alanaatii {portal_name}'
    
    action_text = "reset your password" if is_reset else "update your profile password"
    body = (
        f'Hello,\n\n'
        f'You requested to {action_text} in the Alanaatii {portal_name} Portal.\n'
        f'Your 6-digit verification code is:\n\n'
        f'      {code}\n\n'
        f'This code will expire in 10 minutes.\n'
        f'If you did not request this, please ignore this email.\n\n'
        f'Alanaatii System'
    )
    send_email(to_email, subject, body)

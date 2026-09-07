import os
import boto3
import io
import markdown
import uuid
import logging
from xhtml2pdf import pisa
from botocore.exceptions import NoCredentialsError, ClientError
from backend.config import config

logger = logging.getLogger(__name__)

def generate_markdown_from_itinerary(itinerary: dict) -> str:
    md = f"# Trip to {itinerary.get('destination', 'Unknown')}\n\n"
    md += f"**Total Budget:** ${itinerary.get('total_budget', 0):.2f}\n\n"
    md += f"**Estimated Cost:** ${itinerary.get('estimated_cost', 0):.2f}\n\n"
    
    flights = itinerary.get("flights", [])
    if flights:
        md += "## Flights\n"
        for f in flights:
            md += f"- **{f.get('airline')}** ({f.get('flight_number')}): {f.get('departure_time')} -> {f.get('arrival_time')} | **${f.get('estimated_price', 0):.2f}**\n"
        md += "\n"
        
    hotels = itinerary.get("hotels", [])
    if hotels:
        md += "## Hotels\n"
        for h in hotels:
            rating = f"{h.get('rating')} Stars" if h.get("rating") else "No Rating"
            md += f"- **{h.get('name')}** - {h.get('address')} | {rating} | **${h.get('price_per_night', 0):.2f}/night**\n"
        md += "\n"
        
    daily_plans = itinerary.get("daily_plans", [])
    if daily_plans:
        md += "## Daily Itinerary\n"
        for day in daily_plans:
            md += f"### Date: {day.get('date')} (Est. Daily Cost: ${day.get('daily_cost_estimate', 0):.2f})\n"
            md += f"- **Morning:** {day.get('morning_activity')}\n"
            md += f"- **Afternoon:** {day.get('afternoon_activity')}\n"
            md += f"- **Evening:** {day.get('evening_activity')}\n\n"
            
    warning = itinerary.get("warning_note")
    if warning:
        md += f"---\n*Note: {warning}*\n"
        
    return md

def create_itinerary_pdf(itinerary: dict) -> str:
    """Converts the itinerary dict to PDF binary data using markdown and xhtml2pdf."""
    md_content = generate_markdown_from_itinerary(itinerary)
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #333333; }}
            h1, h2, h3 {{ color: #111111; margin-top: 20px; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border: 1px solid #dddddd; }}
            code {{ font-family: Courier, monospace; background-color: #f9f9f9; padding: 2px 4px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #cccccc; padding: 8px; text-align: left; }}
            th {{ background-color: #eeeeee; font-weight: bold; }}
            a {{ color: #0066cc; text-decoration: none; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(styled_html), dest=result)
    
    if pisa_status.err:
        raise Exception("PDF generation failed.")
        
    # Write to a temp file because upload_to_s3 expects a file_path
    temp_file = f"temp_{uuid.uuid4()}.pdf"
    with open(temp_file, "wb") as f:
        f.write(result.getvalue())
        
    return temp_file

def upload_to_s3(file_path: str) -> str:
    s3 = boto3.client(
        's3',
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        region_name=config.AWS_REGION
    )
    bucket_name = config.AWS_BUCKET_NAME
    object_name = f"itineraries/{uuid.uuid4()}.pdf"
    
    try:
        s3.upload_file(file_path, bucket_name, object_name, ExtraArgs={'ContentType': 'application/pdf'})
        
        # Generate presigned URL (valid for 24 hours)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=86400
        )
        return url
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        return ""

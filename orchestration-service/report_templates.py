"""Templates for reports HTML headers, CSS, any JS"""
class ReportTemplate:
    """Static method for reports. Headers, footers, and item listings"""

    @staticmethod
    def job_html_header():
        """HTML Headers for Job Report"""
        return """<!DOCTYPE html>
<html>
<head>
<title>Chicken Dance Job Report</title>
<style>
ul {{
    background: #e1e1e1;
    border: 1px solid;
    border-top: .5rem solid;
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
   }}
li {{ padding: .5em }}
</style>
</head>

<body>"""


    @staticmethod
    def job_html_footer():
        """HTML Footer For Job Report"""
        return "</body></html>"

    @staticmethod
    def job_html(job):
        """HTML Template For Job Report"""
        job_as_dict = job.as_dict()
        return f"""        <ul>
        <li> Job ID: {job_as_dict.job_id}</li>
        <li> Job Status: {job_as_dict.status}</li>
        <li> Last Block Processed: {job_as_dict.last_block_processed}</li>
        <li> Start Time: {job_as_dict.start_time}</li>
        <li> End Time: {job_as_dict.end_time}</li>
        <li> Integrity Hash: {job_as_dict.actual_integrity_hash}</li>
        <li> Start Block: {job_as_dict.start_block_num}</li>
        <li> End Block: {job_as_dict.end_block_num}</li>
        <li> Configuration ID: {job_as_dict.replay_slice_id}</li>
    </ul>
"""

    @staticmethod
    def job_text_header():
        """Text Header for Job Report"""
        return "      JOB REPORT              \n-------------------------------------\n"

    @staticmethod
    def job_text_footer():
        """Text Footer for Job Report"""
        return "--------------- END ------------------\n"

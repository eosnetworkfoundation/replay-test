"""Templates for reports HTML headers, CSS, any JS"""
class ReportTemplate:
    """Static method for reports. Headers, footers, and item listings"""

    @staticmethod
    def status_html_report(results):
        """HTML Report"""
        # Converting to simple HTML representation (adjust as needed)
        content = ReportTemplate.status_html_header()
        for config in results:
            content += ReportTemplate.status_html(config)
        content += ReportTemplate.status_html_footer()
        return content

    @staticmethod
    def status_html_header():
        """HTML Headers for Status Report"""
        return """<!DOCTYPE html>
<html>
<head>
<title>Chicken Dance Status Report</title>
<style>
ul {
    background: #e1e1e1;
    border: 1px solid;
    border-top: .5rem solid;
    border-top-left-radius: 5px;
    border-bottom-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    width: 32em;
   }
li { padding: .5em }
</style>
</head>

<body>
<h2>Chicken Dance Status Report</h2>
"""


    @staticmethod
    def status_html_footer():
        """HTML Footer For Status Report"""
        return "</body></html>"

    @staticmethod
    def status_html(this_slice):
        """HTML Template For Status Report"""
        return f"""        <ul>
        <li> Replay Slice Id: {this_slice.slice_config.replay_slice_id}</li>
        <li> Job Status: {this_slice.status.name}</li>
        <li> Last Block Processed: {this_slice.last_block_processed}</li>
        <li> Start Time: {this_slice.start_time}</li>
        <li> End Time: {this_slice.end_time}</li>
        <li> Integrity Hash: {this_slice.actual_integrity_hash}</li>
        <li> Start Block: {this_slice.slice_config.start_block_id}</li>
        <li> End Block: {this_slice.slice_config.end_block_id}</li>
    </ul>
"""

    @staticmethod
    def status_text_report(results):
        """TEXT Report"""
        # Converting to simple HTML representation (adjust as needed)
        content = ReportTemplate.status_text_header()
        for config in results:
            content += ReportTemplate.status_text(config)
        content += ReportTemplate.status_text_footer()
        return content

    @staticmethod
    def status_text_header():
        """Text Header for Status Report"""
        return "      JOB REPORT              \n-------------------------------------\n"

    @staticmethod
    def status_text(this_slice):
        """Text Template For Status Report"""
        return f""" Replay Slice Id: {this_slice.slice_config.replay_slice_id}
    Job Status: {this_slice.status.name}
    Last Block Processed: {this_slice.last_block_processed}
    Start Time: {this_slice.start_time}
    End Time: {this_slice.end_time}
    Integrity Hash: {this_slice.actual_integrity_hash}
    Start Block: {this_slice.slice_config.start_block_id}
    End Block: {this_slice.slice_config.end_block_id}\n"""

    @staticmethod
    def status_text_footer():
        """Text Footer for Status Report"""
        return "--------------- END ------------------\n"

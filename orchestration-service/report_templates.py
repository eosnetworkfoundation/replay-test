"""Templates for reports HTML headers, CSS, any JS"""
class ReportTemplate:
    """Static method for reports. Headers, footers, and item listings"""

    @staticmethod
    def home_html_report():
        """HTML HOME Page"""
        content = ReportTemplate.status_html_header()
        content += f"""
        <!DOCTYPE html>
<html>
<body>
<title>Chicken Dance Index Page</title>
<h2>Chicken Dance Index Page</h2>
<a href="/status">Status</a>: shows current jobs and status of each job</br>
<a href="/config?sliceid=1">Config</a>: must specify a sliceid, detailed config supporting job</br>
<a href="/summary">Result Summary</a>: progress or final summary</br>
Job: get and set job configuration. Requires jobid param. Not available on this page.
</body>
</html>
        """
        content += ReportTemplate.status_html_footer()
        return content

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
        <li> Start Block: {this_slice.slice_config.start_block_id}</li>
        <li> End Block: {this_slice.slice_config.end_block_id}</li>
        <li> Start Block Integrity Hash: {this_slice.start_block_integrity_hash}</li>
        <li> End Block Integrity Hash: {this_slice.actual_integrity_hash}</li>
        <li> Expected End Block Integ Hash: {this_slice.slice_config.expected_integrity_hash}<li>
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
    Start Block: {this_slice.slice_config.start_block_id}
    End Block: {this_slice.slice_config.end_block_id}
    Start Block Integrity Hash: {this_slice.start_block_integrity_hash}
    End Block Integrity Hash: {this_slice.actual_integrity_hash}
    Expected End Block Integ Hash: {this_slice.slice_config.expected_integrity_hash}\n"""

    @staticmethod
    def status_text_footer():
        """Text Footer for Status Report"""
        return "--------------- END ------------------\n"

    @staticmethod
    def config_html_report(config):
        """HTML Report"""
        # Converting to simple HTML representation (adjust as needed)
        content = ReportTemplate.config_html_header()
        content += ReportTemplate.config_html(config)
        content += ReportTemplate.config_html_footer()
        return content

    @staticmethod
    def config_html_header():
        """HTML Headers for Config Report"""
        return """<!DOCTYPE html>
<html>
<head>
<title>Replay Config</title>
<style>
ul {
    background: #ADD8E6;
    border: 1px solid;
    border-color: #996666;
    border-top: .5rem solid #996666;
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
<h2>Replay Config</h2>
"""
    @staticmethod
    def config_html(this_slice):
        """HTML Template For Config Report"""
        return f"""        <ul>
        <li> Replay Slice Id: {this_slice.replay_slice_id}</li>
        <li> Start Block Id: {this_slice.start_block_id}</li>
        <li> End Block Id: {this_slice.end_block_id}</li>
        <li> Snapshot Path: {this_slice.snapshot_path}</li>
        <li> Storage Type: {this_slice.storage_type}</li>
        <li> End Block Expected Integrity Hash: {this_slice.expected_integrity_hash}</li>
        <li> Leap Version: {this_slice.leap_version}</li>
    </ul>
"""

    @staticmethod
    def config_html_footer():
        """HTML Footer For Config Report"""
        return "</body></html>"

    @staticmethod
    def summary_text_header():
        """Plain Text Header for Summary Report"""
        return "      SUMMARY REPORT              \n-------------------------------------\n"

    @staticmethod
    def summary_text_report():
        """Plain Text Summary Report"""
        content = ReportTemplate.summary_text_header()
        content += "empty"
        content += ReportTemplate.summary_text_footer()
        return content

    @staticmethod
    def summary_text_footer():
        """Plain Text Header for Summary Report"""
        return "--------------- END ------------------\n"

    @staticmethod
    def summary_html_header():
        """HTML Header for Summary Report"""
"""<!DOCTYPE html>
<html>
<head>
<title>Summary Report</title>
<style>
ul {
background: #d7e5fe;
border: 1px solid;
border-color: #f61e09;
border-top: .5rem solid #f61e09;
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
<h2>Summary Report</h2>
"""

    @staticmethod
    def summary_html_report():
        """HTML Summary Report"""
        content = ReportTemplate.summary_html_header()
        content += "empty"
        content += ReportTemplate.summary_html_footer()
        return content

    @staticmethod
    def config_html_footer():
        """HTML Footer For Summary Report"""
        return "</body></html>"

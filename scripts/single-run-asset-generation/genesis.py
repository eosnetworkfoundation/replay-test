"""produces genesis url on cloud store"""
class Genesis: # pylint: disable=too-few-public-methods
    """return URL for Genesis json file"""
    @staticmethod
    def cloud_url(store, source):
        """convience func to return url to file"""
        return f"s3://{store}/{source}/{source}-genesis.json"

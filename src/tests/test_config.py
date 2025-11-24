from config import config


def test_config_urls():
    mongo_url = config.mongo_url
    assert mongo_url.startswith('mongodb')
    assert config.service.webhook_path in config.webhook_url

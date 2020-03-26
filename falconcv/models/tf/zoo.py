import os
from urllib.parse import urlparse
import markdown
import requests
from bs4 import BeautifulSoup
from falconcv.util import FileUtil
from .downloader import ModelDownloader
from pick import pick
import logging
logger=logging.getLogger(__name__)


class ModelZoo:
    @classmethod
    def pick_od_model(cls):
        # pip install windows-curses
        return pick(list(cls.available_models().keys()),"pick the model")[0]

    @classmethod
    def pick_od_pipeline(cls):
        # pip install windows-curses
        return pick(list(cls.available_pipelines().keys()),"pick the pipeline")[0]

    @staticmethod
    def available_models(arch=None) -> []:
        try:
            models={}
            r=requests.get(os.environ["TF_OBJECT_DETECTION_MODEL_ZOO_URI"])
            if r.status_code == 200:
                md=markdown.Markdown()
                html=md.convert(r.text)
                soup=BeautifulSoup(html,"lxml")
                for a in soup.find_all('a',href=True):
                    model_url=a['href']
                    model_name=a.get_text()
                    path=urlparse(model_url).path
                    ext=os.path.splitext(path)[1]
                    if ext == ".gz":
                        models[model_name]=model_url
            if arch:
                assert arch in ["ssd","faster", "mask"],"Invalid arch param"
                models={k: v for k,v in models.items() if k.startswith(arch)}
            return models
        except Exception as e:
            logger.error("Error listing the models : {}".format(e))

    @classmethod
    def available_pipelines(cls):
        try:
            uri=os.environ["TF_OBJECT_DETECTION_MODEL_CONFIG_URI"]
            response=requests.get(uri)
            config_files={}
            if response.status_code == 200:
                for f in response.json():
                    name=f["name"]
                    url=f["html_url"] \
                        .replace("blob","raw")
                    filename,ext=os.path.splitext(name)
                    if ext == ".config":
                        config_files[filename]=url
            return config_files
        except Exception as e:
            logger.error("Error listing the pipelines : {}".format(e))

    @classmethod
    def download_model(cls,model_name: str,out_folder: str,clear_folder: bool = False):
        try:
            models=cls.available_models()
            assert model_name in models,"Invalid model name or not supported"
            if clear_folder:
                FileUtil.clear_folder(out_folder)
            out_folder=os.path.join(out_folder,model_name)
            return ModelDownloader.download_od_api_model(models[model_name],out_folder)
        except Exception as e:
            logger.error("Error downloading the model : {}".format(e))

    @classmethod
    def download_pipeline(cls,model_name: str,out_folder: str,clear_folder: bool = False):
        try:
            pipelines: dict=cls.available_pipelines()
            assert model_name in pipelines,"Invalid model name or there is not a pipeline available for that model "
            out_folder=os.path.join(out_folder,model_name)
            return ModelDownloader.download_od_api_config(pipelines[model_name],out_folder)
        except Exception as e:
            logger.error("Error downloading the model : {}".format(e))

import pymongo
from info import DATABASE_URI, DATABASE_NAME
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]


async def add_admingroup(group_id, template):
    mycol = mydb["templatedb"]
    mydict = {"group_id": str(group_id), "template": str(template)}

    try:
        x = mycol.insert_one(mydict)
    except Exception:
        logger.exception('Some error occured!', exc_info=True)


async def remove_admingroup(group_id):
    mycol = mydb["templatedb"]
    myquery = {"group_id": str(group_id)}
    mycol.delete_one(myquery)


async def get_admingroup(group_id):
    mycol = mydb["templatedb"]
    myquery = {"group_id": str(group_id), }
    mydoc = mycol.find(myquery)
    return mydoc[0]

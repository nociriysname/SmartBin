from io import BytesIO
import json
from typing import Annotated, AsyncGenerator

from fastapi import Depends, UploadFile
from minio import Minio
from pandas import read_excel

from src.backend.core.exc.exceptions.exceptions import BadRequestError
from src.backend.core.utils.minio import get_minio_client
from src.backend.schemes.files import XLSProductDTO

__all__ = ("MinIOClientDep", "ValidatedXLSFileDep")


async def validate_xls_file(
        file: UploadFile,
) -> AsyncGenerator[list[XLSProductDTO], None]:
    if file.content_type not in [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        raise BadRequestError("Not valuable file type")

    try:
        content = await file.read()
        df = read_excel(BytesIO(content))
        required_columns = {"name", "cost", "article", "barcode", "item_type",
                            "dekart_parameters"}
        if not required_columns.issubset(df.columns):
            raise BadRequestError(
                "XLS-файл должен содержать колонки: "
                "name, cost, article, barcode, item_type, dekart_parameters",
            )

        products = []
        for _, row in df.iterrows():
            try:
                dekart_params = row["dekart_parameters"]
                if isinstance(dekart_params, str):
                    try:
                        dekart_params = json.loads(dekart_params)
                    except json.JSONDecodeError:
                        dekart_params = [float(x) for x in
                                         dekart_params.split(",")]

                if not isinstance(dekart_params, (list, tuple)):
                    raise ValueError(
                        "dekart_parameters должен быть списком чисел")

                product = XLSProductDTO(
                    name=str(row["name"]),
                    cost=float(row["cost"]),
                    article=str(row["article"]),
                    barcode=str(row["barcode"]),
                    item_type=str(row["item_type"]),
                    dekart_parameters=[float(x) for x in dekart_params],
                    product_link=str(
                        row["product_link"]) if "product_link" in row and row[
                        "product_link"] else None,
                )
                products.append(product)
            except Exception as e:
                raise BadRequestError(f"Ошибка в строке XLS: {str(e)}")

        yield products
    except Exception as e:
        raise BadRequestError(f"Ошибка обработки XLS-файла: {str(e)}")
    finally:
        await file.close()

MinIOClientDep = Annotated[Minio, Depends(get_minio_client)]
ValidatedXLSFileDep = Annotated[
    list[XLSProductDTO], Depends(validate_xls_file)]

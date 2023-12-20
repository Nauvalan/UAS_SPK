from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import data_toko as data_tokoModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'kelengkapan_barang': 5, 'lama_kadaluarsa': 5, 'harga_rata_rata': 5, 'jarak_supplier': 3,'jarak_transportasi':3}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(data_tokoModel.nama_toko,  data_tokoModel.kelengkapan_barang, data_tokoModel.lama_kadaluarsa, data_tokoModel.harga_rata_rata, data_tokoModel.jarak_supplier)
        result = session.execute(query).fetchall()
        print(result)
        return [{'nama_toko': data_toko.nama_toko, 'kelengkapan_barang': data_toko.kelengkapan_barang, 'lama_kadaluarsa': data_toko.lama_kadaluarsa, 'harga_rata_rata': data_toko.harga_rata_rata, 'jarak_supplier': data_toko.jarak_supplier} for data_toko in result]

    @property
    def normalized_data(self):
        
        kelengkapan_barang_values = []
        lama_kadaluarsa_values = []
        harga_rata_rata_values = []
        jarak_supplier_values = []

        for data in self.data:

            kelengkapan_barang_values.append(data['kelengkapan_barang'])
            lama_kadaluarsa_values.append(data['lama_kadaluarsa'])
            harga_rata_rata_values.append(data['harga_rata_rata'])
            jarak_supplier_values.append(data['jarak_supplier'])

        return [
            {'nama_toko': data['nama_toko'],
             
             'kelengkapan_barang': data['kelengkapan_barang'] / max(kelengkapan_barang_values),
             'lama_kadaluarsa': data['lama_kadaluarsa'] / max(lama_kadaluarsa_values),
             'harga_rata_rata': data['harga_rata_rata'] / max(harga_rata_rata_values),
             'jarak_supplier': data['jarak_supplier'] / max(jarak_supplier_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
               
                row['kelengkapan_barang'] ** self.raw_weight['kelengkapan_barang'] *
                row['lama_kadaluarsa'] ** self.raw_weight['lama_kadaluarsa'] *
                row['harga_rata_rata'] ** self.raw_weight['harga_rata_rata'] *
                row['jarak_supplier'] ** self.raw_weight['jarak_supplier']
            )

            produk.append({
                'nama_toko': row['nama_toko'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'nama_toko': product['nama_toko'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['nama_toko']:
                  round(
                        row['kelengkapan_barang'] * weight['kelengkapan_barang'] +
                        row['lama_kadaluarsa'] * weight['lama_kadaluarsa'] +
                        row['harga_rata_rata'] * weight['harga_rata_rata'] +
                        row['jarak_supplier'] * weight['jarak_supplier'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class data_toko(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(data_tokoModel)
        data = [{'nama_toko': data_toko.nama_toko, 'kelengkapan_barang': data_toko.kelengkapan_barang, 'lama_kadaluarsa': data_toko.lama_kadaluarsa, 'harga_rata_rata': data_toko.harga_rata_rata, 'jarak_supplier': data_toko.jarak_supplier} for data_toko in session.scalars(query)]
        return self.get_paginated_result('data_toko/', data, request.args), HTTPStatus.OK.value


api.add_resource(data_toko, '/data_toko')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
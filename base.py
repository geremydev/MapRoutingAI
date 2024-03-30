import psutil
from geopy.distance import geodesic
from lxml import etree
import conf
import googlemaps
import folium
import os
import heapq


class Nodo:
    def __init__(self, long, lat, costo=0, padre=None, id=None):
        self.id = id
        self.long = long
        self.lat = lat
        self.costo = costo
        self.padre = padre
        self.lista_vecinos = obtener_nodos_conectados(self.id)

    def __lt__(self, other):
        return self.costo < other.costo


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return not self.elements

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)


def Obj_Instance(instancia_id: str, nodo_que_instancia=None, myOSM=conf.myOSM):
    tree = etree.parse(myOSM)
    root = tree.getroot()
    xpath_nodo = f".//node[@id='{instancia_id}']"
    nodo = root.find(xpath_nodo)
    if nodo is not None:
        latitud = float(nodo.get('lat'))
        longitud = float(nodo.get('lon'))
        id = nodo.get('id')
        instancia = Nodo(longitud, latitud, padre=nodo_que_instancia, id=id)
        instancia.costo = distancia(instancia.padre,
                                    instancia) + instancia.padre.costo if instancia.padre is not None else 0
        return instancia


def distancia(nodo_inicial: Nodo, nodo_objetivo: Nodo):
    if nodo_inicial is None:
        return 0
    else:
        return geodesic((nodo_inicial.lat, nodo_inicial.long), (nodo_objetivo.lat, nodo_objetivo.long)).meters


def calculate_total_cost(nodo_inicial: Nodo, nodo_objetivo: Nodo):
    # C(n) = costo_acumulado_nodo + distanciaAB + tipo de calle
    return nodo_inicial.costo + distancia(nodo_inicial, nodo_objetivo) + heurística2(info_calle(nodo_inicial.id)[1])

def heurística2(tipo_calle: str):
    match tipo_calle:
        case "primary":
            return -100
        case "secondary":
            return -100
        case "tertiary":
            return 100
        case "unclassified":
            return 100
        case _:
            return 0


def info_calle(nodo_id: str, osm_file_path=conf.myOSM):
    # Parsear el archivo OSM local
    tree = etree.parse(osm_file_path)
    root = tree.getroot()

    # Buscar el camino (way) que contiene el nodo con el ID dado como referencia
    way_xpath = f".//way[nd[@ref='{nodo_id}']]"
    way_element = root.xpath(way_xpath)[0]

    if way_element is not None:
        # Buscar la información de la calle y la carretera directamente en el camino encontrado
        nombre_calle = way_element.xpath(".//tag[@k='name']/@v")
        tipo_carretera = way_element.xpath(".//tag[@k='highway']/@v")

        # Obtener los valores (si existen) o establecerlos como None
        nombre_calle = nombre_calle[0] if nombre_calle else None
        tipo_carretera = tipo_carretera[0] if tipo_carretera else None

        return (nombre_calle, tipo_carretera)
    else:
        return None, None


def route_output(ruta_solución: Nodo, objetivo: Nodo, Inicio_memory):
    Final_memory = psutil.virtual_memory().used  # Obtén el uso de memoria final
    Final_memory = abs(Final_memory - Inicio_memory)
    Final_memory = Final_memory / 1024 / 1024
    print("¡CAMINO ENCONTRADO!")
    trayectoria = []
    while ruta_solución.padre:
        trayectoria.append(ruta_solución.padre)
        ruta_solución = ruta_solución.padre
    trayectoria = list(reversed(trayectoria))
    trayectoria.append(objetivo)
    print(f"El consumo de memoria fue: {Final_memory} MB")

    with open('output.txt', 'w') as archivo:
        for i in trayectoria:
            archivo.write(i.id + "\n")
    Construir_mapa()

def obtener_nodos_conectados(nodo_id, myOSM=conf.myOSM):
    tree = etree.parse(myOSM)
    root = tree.getroot()

    # Busca la calle que contiene el nodo con el ID dado
    calle_via_xpath = f".//way[nd[@ref='{nodo_id}'] and tag[@k='highway']]"
    calles_via = root.xpath(calle_via_xpath)

    vecinos_set = set()

    for calle_via in calles_via:
        nd_tags = calle_via.xpath("nd")
        ref_list = [nd.get('ref') for nd in nd_tags]

        try:
            # Encuentra la posición del nodo en la lista de referencias
            indice_nodo = ref_list.index(nodo_id)

            # Verificar si la carretera es de una vía o de dos vías
            oneway_tag = calle_via.find("tag[@k='oneway']")
            es_una_via = oneway_tag is not None and oneway_tag.get('v') == 'yes'

            # Obtener el nodo anterior y el nodo siguiente
            nodo_anterior = ref_list[indice_nodo - 1] if indice_nodo > 0 and not es_una_via else None
            nodo_siguiente = ref_list[indice_nodo + 1] if indice_nodo < len(ref_list) - 1 else None

            if es_una_via:
                if nodo_siguiente is not None:
                    vecinos_set.add(nodo_siguiente)
            else:
                if nodo_anterior is not None:
                    vecinos_set.add(nodo_anterior)
                if nodo_siguiente is not None:
                    vecinos_set.add(nodo_siguiente)


        except ValueError:
            # El nodo no está en la lista de referencias
            pass

    vecinos_set.discard(str(nodo_id))  # Elimina el propio nodo de la lista de vecinos
    return tuple(vecinos_set)


def Detect_Copy():
    import pyperclip

    texto1 = ""
    texto2 = ""

    contador = 0

    texto = pyperclip.paste()

    while True:
        texto_nuevo = pyperclip.paste()
        if texto_nuevo != texto:
            contador += 1
            if contador == 1:
                texto1 = texto_nuevo
                print("Has copiado el primer texto:", texto1)
            elif contador == 2:
                texto2 = texto_nuevo
                print("Has copiado el segundo texto:", texto2)
                break
        texto = texto_nuevo
    texto1 = texto1[5::]
    texto2 = texto2[5::]
    return texto1, texto2


def Construir_mapa():
    gmaps = googlemaps.Client(
        key='AIzaSyC1DPKwMpMAmULE2nLd2ZXG7AhNa8y8fk8')  # Recuerda reemplazar 'TU_API_KEY' con tu clave de API de Google Maps

    ruta = conf.myOSM

    with open("output.txt", 'r') as f:
        coordinates = []
        tree = etree.parse(ruta)
        root = tree.getroot()
        for line in f:
            instancia_id = line.strip()
            # Construye el xpath para buscar el nodo con el ID de la línea
            xpath_nodo = f".//node[@id='{instancia_id}']"
            nodo = root.find(xpath_nodo)

            if nodo is not None:  # Si el nodo existe
                latitud = float(nodo.get('lat'))
                longitud = float(nodo.get('lon'))
                coordinates.append((latitud, longitud))

    path = [{'lat': lat, 'lng': lng} for lat, lng in coordinates]

    polyline = {
        'locations': coordinates,  # Corregido para usar 'path' en lugar de 'coordinates'
        'geodesic': True,
        'strokeColor': '#FF0000',
        'strokeOpacity': 1.0,
        'strokeWeight': 2
    }

    start_point = coordinates[0]
    end_point = coordinates[-1]

    my_map = folium.Map(location=start_point, zoom_start=15)

    # Añadir marcador verde en el punto de inicio
    folium.Marker(location=start_point, popup='Start', icon=folium.Icon(color='green')).add_to(my_map)

    # Añadir marcador rojo en el punto final
    folium.Marker(location=end_point, popup='End', icon=folium.Icon(color='red')).add_to(my_map)

    folium.PolyLine(**polyline).add_to(my_map)

    my_map.save('map_with_polyline_and_markers.html')

    # Abrir el archivo con el programa predeterminado
    os.startfile(f"{conf.root}\map_with_polyline_and_markers.html")

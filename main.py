import conf
import os
from base import *
ruta = conf.myOSM
Inicio_memory = 0

def A_Star(nodo_inicial, nodo_objetivo, Inicio_memory):
    Explorados = set()
    Frontera = PriorityQueue()
    Frontera.put(nodo_inicial, calculate_total_cost(nodo_inicial, nodo_objetivo))
    while Frontera.elements:
        #Extrae el de menor costo
        costo_actual, nodo_actual = Frontera.get()

        #Agregamos el id del nodo explorado
        Explorados.add(nodo_actual.id)
        print("Explorado ", nodo_actual.id)

        if nodo_actual.id == nodo_objetivo.id:
            print("Se alcanzó el camino más eficiente")
            route_output(nodo_actual, nodo_objetivo, Inicio_memory)
            break
    
        vecinos = nodo_actual.lista_vecinos
        
         #Eficientizar, que lo expanda cuando no hayan nodos vías extra por explorar
        for vecino in vecinos:
            vecino = Obj_Instance(vecino, nodo_actual)
            costo_vecino = calculate_total_cost(vecino, nodo_objetivo)
            if vecino.id not in Explorados and vecino not in (tupla[1] for tupla in Frontera.elements):
                print("Add Frontera, ", vecino.id)
                Frontera.put(vecino, costo_vecino)
            elif vecino in (tupla[1] for tupla in Frontera.elements):
                # El nodo ya está en la frontera, pero verificamos si la nueva ruta es más barata
                costo_existente = next(tupla[0] for tupla in Frontera.elements if tupla[1] == vecino)
                if costo_vecino < costo_existente:
                    # Eliminar el nodo existente de la frontera
                    Frontera.elements = [(costo, nodo) for costo, nodo in Frontera.elements if nodo != vecino]
                    # Agregar el nodo vecino con el nuevo costo a la frontera
                    Frontera.put(vecino, costo_vecino)





def main():
#Reemplaza "JOSM.exe" con el nombre del ejecutable de la aplicación que quieres abrir
    if not "JOSM.exe" in (p.name() for p in psutil.process_iter()):
        os.startfile(conf.JosmFilePath)
    origen, destino = Detect_Copy()
    origen = Obj_Instance(origen)
    destino = Obj_Instance(destino) 

    Inicio_memory =  psutil.virtual_memory().used 
    A_Star(origen, destino, Inicio_memory)

if __name__ == '__main__':
    main()
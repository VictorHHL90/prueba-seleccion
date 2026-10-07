**DÍA 1 CONFIGURACIÓN AVANZADA DE LA INFRAESTRUCTURA DE**

GCP

Objetivos:

● Evaluar la capacidad de crear y configurar un entorno seguro y

escalable en GCP.

● Poner a prueba habilidades en scripting, manejo de APIs y diseño de

arquitectura en la nube.

Tareas Detalladas:

1\. Creación y Configuración del Proyecto:

○ Crear un proyecto nuevo en GCP.

○ Habilitar las siguientes APIs: Cloud Storage, Cloud Functions,

Cloud Pub/Sub, Cloud Logging y, opcionalmente, Cloud Build.

○ Configurar roles y permisos mediante IAM, creando un usuario de

prueba con privilegios mínimos para simular un entorno de

producción controlado.



2\. Diseño de Almacenamiento y Automatización Inicial:

○ Crear un bucket en Cloud Storage con:

■ Configuración de reglas de ciclo de vida (lifecycle) para

gestionar la retención y eliminación de archivos.

■ Políticas de acceso refinadas (por ejemplo, roles específicos

para lectura/escritura).



○ Desarrollar una Cloud Function (utilizando Python o Node.js) que

se active automáticamente al subir un archivo al bucket.

■ La función debe extraer metadatos del archivo (nombre,

tamaño, tipo) y registrar eventos en Cloud Logging.

■ Incluir manejo robusto de errores y registros detallados

(logging) para facilitar la depuración.



3\. Pruebas y Documentación:



○ Implementar pruebas unitarias básicas para la Cloud Function,

verificando tanto el flujo exitoso como el manejo de errores.

○ Documentar el proceso en un repositorio de código (por ejemplo,

GitHub), incluyendo:

■ Un README con instrucciones paso a paso, capturas de

pantalla y diagramas del flujo de trabajo.

■ Comentarios en el código explicando las decisiones

técnicas y configuraciones aplicadas.
---------------------------------------------------------------------------------
**Actividades Realizadadas.**

El sistema implementa un flujo serverless que detecta automáticamente la carga de archivos en Google Cloud Storage, procesa los metadatos del archivo mediante una Cloud Function y registra la información en Cloud Logging.

**Flujo**

Se carga un archivo en el bucket de Cloud Storage.

Cloud Storage genera un evento cuando el objeto es finalizado.

Eventarc recibe y enruta el evento.

La Cloud Function process-file-upload procesa el evento.

La función obtiene los metadatos principales del archivo:

Nombre

Tamaño

Tipo MIME

Bucket de origen

La información se registra en Cloud Logging.

Si ocurre un error, se registra el detalle y la excepción se propaga para que la plataforma pueda detectar el fallo.

**Configuración de Google Cloud**

Proyecto

Project ID: prueba-seleccion-510716

Región



La infraestructura principal de procesamiento utiliza:



us-central1



La región del bucket y la del trigger se configuraron de forma compatible para permitir el procesamiento de eventos de Cloud Storage mediante Eventarc.



**Cloud Storage**



Bucket utilizado:



prueba-seleccion-510716-file-upload-us

Lifecycle



Se configuró una regla de ciclo de vida para eliminar automáticamente los objetos después de 30 días.



Esto permite evitar la acumulación indefinida de archivos de prueba y controlar el almacenamiento utilizado.



**IAM y seguridad**



Se creó una cuenta de servicio de prueba:



test-seleccion@prueba-seleccion-510716.iam.gserviceaccount.com



La cuenta dispone únicamente del rol:



roles/storage.objectViewer



Este permiso permite consultar objetos de Cloud Storage sin conceder permisos de modificación o administración.



Se aplicó el principio de mínimo privilegio para limitar el acceso de la cuenta de prueba.



El bucket utiliza:



Acceso uniforme a nivel de bucket.

Prevención de acceso público.

Permisos específicos para los servicios que participan en el procesamiento de eventos.

Cloud Function



Nombre:



process-file-upload



Características:



Runtime: Python 3.13

Generación: Cloud Functions Gen 2

Región: us-central1

Trigger: Cloud Storage object finalized



La función se encuentra en:



function/main.py

Metadatos procesados



La función obtiene del evento:



name

size

contentType

bucket



Ejemplo de información registrada:



Evento de Cloud Storage recibido |

bucket=prueba-seleccion-510716-file-upload-us |

nombre=prueba-5.txt |

tamaño=34 bytes |

tipo=text/plain



Posteriormente registra:



Archivo procesado correctamente |

nombre=prueba-5.txt

**Manejo de errores**



La función utiliza un bloque try/except para controlar errores durante el procesamiento.



Si el evento no contiene el nombre del archivo, se genera un ValueError.



Los errores se registran mediante logger.exception() para conservar información útil para diagnóstico y posteriormente se vuelve a lanzar la excepción.



Esto evita ocultar errores y permite que la plataforma detecte correctamente una ejecución fallida.



Logging



Se utiliza el módulo estándar logging de Python.



La configuración permite enviar los mensajes generados por la función a stdout, donde son capturados automáticamente por Cloud Logging.



Se utilizan diferentes niveles de información:



INFO  -> procesamiento correcto

ERROR -> errores durante el procesamiento



La configuración de logging utiliza force=True para garantizar que la configuración aplicada por la función sea efectiva en el entorno administrado de Cloud Functions.



Pruebas unitarias



Las pruebas se encuentran en:



function/test-unitarias.py



Se implementaron pruebas para:



Caso exitoso



Verifica que un evento válido:



sea procesado correctamente;

devuelva estado success;

conserve el nombre;

conserve el tamaño;

conserve el tipo MIME;

conserve el bucket;

genere los logs esperados.

Evento sin nombre de archivo



Verifica que se genere:



ValueError



cuando el evento no contiene el nombre del archivo.



Evento vacío



Verifica que un evento sin datos también sea rechazado correctamente.



Resultado



Las pruebas fueron ejecutadas mediante:



.venv\\Scripts\\python.exe -m pytest .\\function\\test-unitarias.py



Resultado:



3 passed

Despliegue



Desde el directorio function se puede desplegar la función mediante:



gcloud functions deploy process-file-upload `

&#x20; --gen2 `

&#x20; --runtime=python313 `

&#x20; --region=us-central1 `

&#x20; --source=. `

&#x20; --entry-point=process\_file\_upload `

&#x20; --trigger-bucket=prueba-seleccion-510716-file-upload-us
Finalmente
Se realizaron múltiples cargas de archivos de prueba para validar el funcionamiento del sistema.



Entre los archivos utilizados se encuentran:



prueba.txt

prueba-2.txt

prueba-3.txt

prueba-4.txt

prueba-5.txt



Cada carga permitió verificar la recepción del evento y el procesamiento de sus metadatos.



Evidencias



Las capturas de pantalla del proyecto se almacenarán en:



docs/screenshots/

Día 3 — Integración GCP + Google Workspace

Se implementó una integración entre Google Cloud Platform y Google Workspace para automatizar el procesamiento de archivos cargados en Cloud Storage.

Arquitectura
Cloud Storage -> Cloud Function (Python 3.13) -> Validación de metadatos -> HMAC-SHA256 + Secret Manager -> Apps Script Web App -> Google Sheets + Gmail

Componentes implementados
Cloud Storage: almacenamiento de archivos y disparador del flujo.
Cloud Function: procesa eventos de archivos y extrae sus metadatos.
Secret Manager: almacenamiento seguro del secreto utilizado para la autenticación.
HMAC-SHA256: validación de autenticidad e integridad de la información.
Google Apps Script: recibe y valida los metadatos mediante HTTPS.
Google Sheets: registra automáticamente los archivos recibidos.
Gmail/Google Groups: envía una notificación cuando se recibe un archivo.
Cloud Logging: permite consultar la ejecución y errores del proceso.
Seguridad

Se implementaron validaciones de los metadatos recibidos, cuentas de servicio con permisos específicos y almacenamiento del secreto en Secret Manager. La comunicación entre Cloud Function y Apps Script utiliza HTTPS y una firma HMAC-SHA256.

Pruebas

Se realizaron pruebas unitarias y de integración.

5 pruebas unitarias aprobadas.
Prueba de carga de archivos en Cloud Storage.
Prueba de comunicación con Apps Script.
Prueba de registro automático en Google Sheets.
Prueba de envío de notificación por correo.
Prueba de firma HMAC inválida.
Verificación de logs en Cloud Logging.
Resultado

El flujo completo quedó funcionando de extremo a extremo:

Cloud Storage → Cloud Function → Apps Script → Google Sheets + Gmail

La integración fue validada mediante pruebas reales y evidencias de ejecución.
CREATE TABLE public.perfil (
    id SERIAL PRIMARY KEY,
    publicacion_id INTEGER REFERENCES public.publicacion(id),
    nickname VARCHAR(255),
    username VARCHAR(255),
    enlace VARCHAR(255),
    likes VARCHAR(255), -- Considera usar INTEGER si es un contador de likes
    extraido_en TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP -- Columna para almacenar la hora de extracción
);


CREATE TABLE public.user_scraper (
    id SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(255) , -- El nombre del usuario que usa el scraper
    correo_usuario VARCHAR(255) , -- Correo del usuario (si lo deseas)
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP -- Fecha de registro del usuario
);

-- Tabla para almacenar los temas (topics) que se pueden buscar
CREATE TABLE public.busqueda (
    id SERIAL PRIMARY KEY,
    busqueda VARCHAR(255),
    typo TEXT, -- Descripción del tema (si lo deseas)
    tiempo TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP -- Fecha de creación o extracción
);


CREATE TABLE public.publicacion (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(255),
    enlace VARCHAR(255),
    descripcion TEXT,
    fecha TIMESTAMPTZ,
    likes VARCHAR(255),
    extraido_en TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP -- Columna para almacenar la hora de extracción
);

CREATE TABLE public.video (
    id SERIAL PRIMARY KEY,
    url TEXT,
    publicacion_id INTEGER REFERENCES public.publicacion(id),
    extraido_en TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP -- Columna para almacenar la hora de extracción
);

CREATE TABLE public.user_scraper_perfil (
    user_scraper_id INTEGER REFERENCES public.user_scraper(id),
    perfil_id INTEGER REFERENCES public.busqueda(id),
    fecha_busqueda TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_scraper_id, perfil_id) -- Relación única entre usuario y perfil
);
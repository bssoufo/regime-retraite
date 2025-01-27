<?php
/*
Plugin Name: SharePoint Connect
Plugin URI: https://votre-site.com/sharepoint-connect
Description: Connecte Formidable Forms à SharePoint.
Version: 1.3
Author: Votre Nom
Author URI: https://votre-site.com
License: GPL2
Text Domain: sharepoint-connect
*/

if ( ! defined( 'ABSPATH' ) ) {
    exit; // Exit if accessed directly
}

class SharePoint_Connect {

    private static $instance = null;

    // Plugin settings
    private $settings;

    public static function get_instance() {
        if ( self::$instance == null ) {
            self::$instance = new SharePoint_Connect();
        }
        return self::$instance;
    }

    private function __construct() {
        // Initialize settings
        $this->settings = wp_parse_args( get_option( 'spc_settings', array() ), $this->default_settings() );

        // Admin menu
        add_action( 'admin_menu', array( $this, 'add_admin_menu' ) );

        // Register settings
        add_action( 'admin_init', array( $this, 'register_settings' ) );

        // Enqueue admin styles
        add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_admin_styles' ) );

        // Hook into Formidable Forms
        add_action( 'frm_after_create_entry', array( $this, 'send_files_to_fastapi' ), 10, 2 );

        // Load plugin textdomain for translations
        add_action( 'init', array( $this, 'load_textdomain' ) );
    }

    private function default_settings() {
        return array(
            'form_id'               => '',
            'sharepoint_connect_url'=> '',
            'api_token'             => '',
            'name_field_id'         => '',
            'date_of_birth_field_id'=> '',
            'email_field_id'        => '',
            'files_field_id'        => '',
            'doc_id_key'            => '',
            'doc_type_key'          => '',
            'relative_file_path'    => 'wp-content/documents-private/',
        );
    }

    public function load_textdomain() {
        load_plugin_textdomain( 'sharepoint-connect', false, dirname( plugin_basename( __FILE__ ) ) . '/languages' );
    }

    public function add_admin_menu() {
        add_options_page(
            __( 'SharePoint Connect', 'sharepoint-connect' ),
            __( 'SharePoint Connect', 'sharepoint-connect' ),
            'manage_options',
            'sharepoint-connect',
            array( $this, 'settings_page' )
        );
    }

    public function register_settings() {
        register_setting( 'spc_settings_group', 'spc_settings', array( $this, 'sanitize_settings' ) );

        add_settings_section(
            'spc_main_section',
            __( 'Paramètres Principaux', 'sharepoint-connect' ),
            null,
            'sharepoint-connect'
        );

        // ID du Formulaire
        add_settings_field(
            'form_id',
            __( 'ID du Formulaire', 'sharepoint-connect' ),
            array( $this, 'form_id_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // URL de SharePoint Connect
        add_settings_field(
            'sharepoint_connect_url',
            __( 'URL de SharePoint Connect', 'sharepoint-connect' ),
            array( $this, 'sharepoint_connect_url_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Token API
        add_settings_field(
            'api_token',
            __( 'Token API', 'sharepoint-connect' ),
            array( $this, 'api_token_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Mappings des Champs - Nom
        add_settings_field(
            'name_field_id',
            __( 'Nom', 'sharepoint-connect' ),
            array( $this, 'name_field_id_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Mappings des Champs - Date de Naissance
        add_settings_field(
            'date_of_birth_field_id',
            __( 'Date de Naissance', 'sharepoint-connect' ),
            array( $this, 'date_of_birth_field_id_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Mappings des Champs - Email
        add_settings_field(
            'email_field_id',
            __( 'Email', 'sharepoint-connect' ),
            array( $this, 'email_field_id_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Mappings des Champs - Fichiers
        add_settings_field(
            'files_field_id',
            __( 'Fichiers', 'sharepoint-connect' ),
            array( $this, 'files_field_id_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Clé ID du Document
        add_settings_field(
            'doc_id_key',
            __( 'Clé ID du Document', 'sharepoint-connect' ),
            array( $this, 'doc_id_key_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Clé Type du Document
        add_settings_field(
            'doc_type_key',
            __( 'Clé Type du Document', 'sharepoint-connect' ),
            array( $this, 'doc_type_key_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Chemin Relatif des Fichiers
        add_settings_field(
            'relative_file_path',
            __( 'Chemin Relatif des Fichiers', 'sharepoint-connect' ),
            array( $this, 'relative_file_path_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );
    }

    public function sanitize_settings( $input ) {
        $sanitized = array();

        $sanitized['form_id'] = intval( $input['form_id'] );
        $sanitized['sharepoint_connect_url'] = esc_url_raw( $input['sharepoint_connect_url'] );
        $sanitized['api_token'] = sanitize_text_field( $input['api_token'] );

        $sanitized['name_field_id'] = sanitize_text_field( $input['name_field_id'] );
        $sanitized['date_of_birth_field_id'] = sanitize_text_field( $input['date_of_birth_field_id'] );
        $sanitized['email_field_id'] = sanitize_text_field( $input['email_field_id'] );
        $sanitized['files_field_id'] = sanitize_text_field( $input['files_field_id'] );

        $sanitized['doc_id_key'] = sanitize_text_field( $input['doc_id_key'] );
        $sanitized['doc_type_key'] = sanitize_text_field( $input['doc_type_key'] );
        $sanitized['relative_file_path'] = sanitize_text_field( $input['relative_file_path'] );

        // Logs de débogage
        error_log( "SharePoint Connect: Sanitized settings: " . wp_json_encode( $sanitized ) );
        return $sanitized;
    }

    public function settings_page() {
        ?>
        <div class="wrap">
            <h1><?php _e( 'SharePoint Connect', 'sharepoint-connect' ); ?></h1>
            <form method="post" action="options.php">
                <?php
                settings_fields( 'spc_settings_group' );
                do_settings_sections( 'sharepoint-connect' );
                submit_button();
                ?>
            </form>
        </div>
        <?php
    }

    // Callbacks pour chaque champ individuel

    // ID du Formulaire
    public function form_id_callback() {
        printf(
            '<input type="number" id="form_id" name="spc_settings[form_id]" value="%s" />',
            esc_attr( $this->settings['form_id'] )
        );
        echo '<p class="description">' . __( 'Entrez l\'ID du formulaire Formidable Forms que vous souhaitez connecter à SharePoint.', 'sharepoint-connect' ) . '</p>';
    }

    // URL de SharePoint Connect
    public function sharepoint_connect_url_callback() {
        printf(
            '<input type="url" id="sharepoint_connect_url" name="spc_settings[sharepoint_connect_url]" value="%s" size="50" />',
            esc_attr( $this->settings['sharepoint_connect_url'] )
        );
        echo '<p class="description">' . __( 'Entrez l\'URL de votre service SharePoint Connect.', 'sharepoint-connect' ) . '</p>';
    }

    // Token API
    public function api_token_callback() {
        printf(
            '<input type="text" id="api_token" name="spc_settings[api_token]" value="%s" size="50" />',
            esc_attr( $this->settings['api_token'] )
        );
        echo '<p class="description">' . __( 'Entrez votre token API pour authentifier les requêtes vers SharePoint.', 'sharepoint-connect' ) . '</p>';
    }

    // Nom Field ID
    public function name_field_id_callback() {
        printf(
            '<input type="text" id="name_field_id" name="spc_settings[name_field_id]" value="%s" size="50" />',
            esc_attr( $this->settings['name_field_id'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé qui permet d\'obtenir le nom dans le post du formulaire Formidable Forms.', 'sharepoint-connect' ) . '</p>';
    }

    // Date de Naissance Field ID
    public function date_of_birth_field_id_callback() {
        printf(
            '<input type="text" id="date_of_birth_field_id" name="spc_settings[date_of_birth_field_id]" value="%s" size="50" />',
            esc_attr( $this->settings['date_of_birth_field_id'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé qui permet d\'obtenir la date de naissance dans le post du formulaire Formidable Forms.', 'sharepoint-connect' ) . '</p>';
    }

    // Email Field ID
    public function email_field_id_callback() {
        printf(
            '<input type="text" id="email_field_id" name="spc_settings[email_field_id]" value="%s" size="50" />',
            esc_attr( $this->settings['email_field_id'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé qui permet d\'obtenir l\'email dans le post du formulaire Formidable Forms.', 'sharepoint-connect' ) . '</p>';
    }

    // Fichiers Field ID
    public function files_field_id_callback() {
        printf(
            '<input type="text" id="files_field_id" name="spc_settings[files_field_id]" value="%s" size="50" />',
            esc_attr( $this->settings['files_field_id'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé qui permet d\'obtenir le tableau de fichiers dans le post du formulaire Formidable Forms.', 'sharepoint-connect' ) . '</p>';
    }

    // Clé ID du Document
    public function doc_id_key_callback() {
        printf(
            '<input type="text" id="doc_id_key" name="spc_settings[doc_id_key]" value="%s" size="50" />',
            esc_attr( $this->settings['doc_id_key'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé pour l\'ID du document dans le tableau de fichiers.', 'sharepoint-connect' ) . '</p>';
    }

    // Clé Type du Document
    public function doc_type_key_callback() {
        printf(
            '<input type="text" id="doc_type_key" name="spc_settings[doc_type_key]" value="%s" size="50" />',
            esc_attr( $this->settings['doc_type_key'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé pour le type de document dans le tableau de fichiers.', 'sharepoint-connect' ) . '</p>';
    }

    // Chemin Relatif des Fichiers
    public function relative_file_path_callback() {
        printf(
            '<input type="text" id="relative_file_path" name="spc_settings[relative_file_path]" value="%s" size="50" />',
            esc_attr( $this->settings['relative_file_path'] )
        );
        echo '<p class="description">' . __( 'Chemin relatif vers le répertoire des fichiers attachés.', 'sharepoint-connect' ) . '</p>';
    }

    public function enqueue_admin_styles( $hook ) {
        if ( $hook !== 'settings_page_sharepoint-connect' ) {
            return;
        }
        wp_enqueue_style( 'spc_admin_css', plugin_dir_url( __FILE__ ) . 'assets/css/admin.css', array(), '1.0' );
    }

    /**
     * Fonction principale pour envoyer les fichiers à SharePoint
     */
    public function send_files_to_fastapi( $entry_id, $form_id ) {
        if ( (int) $form_id !== (int) $this->settings['form_id'] ) {
            return; // Ignore si ce n'est pas le bon formulaire
        }

        // Vérifie si $_POST['item_meta'] est défini
        if ( ! isset( $_POST['item_meta'] ) || ! is_array( $_POST['item_meta'] ) ) {
            error_log( "SharePoint Connect: 'item_meta' n'est pas défini ou n'est pas un tableau pour l'entrée ID $entry_id." );
            return;
        }
        $item_meta = $_POST['item_meta'];

        // Récupère les champs mappés depuis les paramètres
        $name_field_id           = isset($this->settings['name_field_id']) ? intval( $this->settings['name_field_id'] ) : null;
        $date_of_birth_field_id  = isset($this->settings['date_of_birth_field_id']) ? intval( $this->settings['date_of_birth_field_id'] ) : null;
        $email_field_id          = isset($this->settings['email_field_id']) ? intval( $this->settings['email_field_id'] ) : null;
        $files_field_id          = isset($this->settings['files_field_id']) ? intval( $this->settings['files_field_id'] ) : null;
        $doc_id_key              = sanitize_text_field( $this->settings['doc_id_key'] );
        $doc_type_key            = sanitize_text_field( $this->settings['doc_type_key'] );


        // Récupère les données de l'entrée via $_POST['item_meta']
        $name          = $name_field_id && isset( $item_meta[ $name_field_id ] ) ? sanitize_text_field( $item_meta[ $name_field_id ] ) : '';
        $date_of_birth = $date_of_birth_field_id && isset( $item_meta[ $date_of_birth_field_id ] ) ? sanitize_text_field( $item_meta[ $date_of_birth_field_id ] ) : '';
        $email         = $email_field_id && isset( $item_meta[ $email_field_id ] ) ? sanitize_email( $item_meta[ $email_field_id ] ) : '';
        $files         = $files_field_id && isset( $item_meta[ $files_field_id ] ) ? $item_meta[ $files_field_id ] : array();

        // Logs de débogage
        error_log( "SharePoint Connect: Récupération des champs pour l'entrée ID $entry_id." );
        error_log( "SharePoint Connect: Nom: $name, Date de Naissance: $date_of_birth, Email: $email" );

        // Vérifie que les fichiers existent et sont sous forme de tableau
        if ( empty( $files ) || ! is_array( $files ) ) {
            error_log( "SharePoint Connect: Aucun fichier trouvé pour l'entrée ID $entry_id." );
            return;
        }

        $files_and_docs = array();
        foreach ( $files as $file ) {
            if ( isset( $file[$doc_id_key ] ) && isset( $file[$doc_type_key] ) ) {
                $file_id  = intval( $file[$doc_id_key] );
                $doc_type = sanitize_text_field( $file[$doc_type_key] );

                $file_path = $this->resolve_file_path( $file_id );

                if ( $file_path && file_exists( $file_path ) ) {
                    $files_and_docs[] = array(
                        'file' => $file_path,
                        'type' => $doc_type
                    );
                } else {
                    error_log( "SharePoint Connect: Fichier introuvable ou non lisible pour l'ID $file_id." );
                }
            } else {
                error_log( "SharePoint Connect: Données de fichier incomplètes pour un des fichiers : " . wp_json_encode($file));
            }
        }

        if ( empty( $files_and_docs ) ) {
            error_log( "SharePoint Connect: Aucun fichier valide trouvé pour l'entrée ID $entry_id." );
            return;
        }

        // Prépare les données POST pour SharePoint
        $post_fields = array(
            'name'          => $name,
            'date_of_birth' => $date_of_birth,
            'email'         => $email,
        );

        // Ajoute les clés Doc ID et Doc Type si elles sont définies
        if ( ! empty( $doc_id_key ) ) {
            $post_fields['doc_id_key'] = $doc_id_key;
        }

        if ( ! empty( $doc_type_key ) ) {
            $post_fields['doc_type_key'] = $doc_type_key;
        }

        foreach ( $files_and_docs as $index => $file_doc ) {
            $file_path = $file_doc['file'];
            $doc_type  = $file_doc['type'];

            if ( file_exists( $file_path ) ) {
                $post_fields[ "file_$index" ]        = new CURLFile( $file_path );
                $post_fields[ "description_$index" ] = $doc_type;
            }
        }


        // Initialise cURL
        $ch = curl_init();

        // Définir les options cURL
        curl_setopt( $ch, CURLOPT_URL, $this->settings['sharepoint_connect_url'] );
        curl_setopt( $ch, CURLOPT_POST, true );
        curl_setopt( $ch, CURLOPT_POSTFIELDS, $post_fields );
        curl_setopt( $ch, CURLOPT_RETURNTRANSFER, true );
        curl_setopt( $ch, CURLOPT_HTTPHEADER, array(
            'Content-Type: multipart/form-data',
            'X-API-Token: ' . $this->settings['api_token']
        ) );

        // Exécuter la requête POST
        $response = curl_exec( $ch );

        // Vérifier les erreurs cURL
        if ( $response === false ) {
            $error = curl_error( $ch );
            error_log( "SharePoint Connect: cURL Error: $error" );
            curl_close( $ch );
            return;
        }

        // Obtenir le code de réponse HTTP
        $http_code = curl_getinfo( $ch, CURLINFO_HTTP_CODE );
        curl_close( $ch );

        // Gérer la réponse
        if ( $http_code >= 200 && $http_code < 300 ) {
            // Succès - Optionnellement traiter la réponse
            // Par exemple, enregistrer une note dans l'entrée
            // update_post_meta( $entry_id, 'spc_response', $response );
        } else {
            // Enregistrer l'erreur
            error_log( "SharePoint Connect: SharePoint responded with status code $http_code. Response: $response" );
        }
    }


    /**
     * Résout le chemin du fichier en fonction de l'ID
     */
    private function resolve_file_path( $file_id ) {
        $relative_path = trailingslashit( $this->settings['relative_file_path'] );
        $file_path_original = get_attached_file( $file_id );

        if ( ! $file_path_original ) {
            error_log( "SharePoint Connect: Impossible de récupérer le chemin du fichier pour l'ID $file_id." );
            return false;
        }

        $file_name = basename( $file_path_original );
        $file_path = ABSPATH . $relative_path . $file_name;

        // Modifier les permissions pour rendre le fichier lisible
        $this->make_file_readable( $file_path );

        // Vérifier si le fichier existe et est lisible
        if ( file_exists( $file_path ) && is_readable( $file_path ) ) {
            return $file_path;
        } else {
            error_log( "SharePoint Connect: Fichier introuvable ou non lisible : $file_path" );
        }

        return false;
    }

    /**
     * Modifie les permissions du fichier pour le rendre lisible
     */
    private function make_file_readable( $file_path ) {
        if ( ! file_exists( $file_path ) ) {
            error_log( "SharePoint Connect: Fichier introuvable : $file_path" );
            return false;
        }

        if ( chmod( $file_path, 0644 ) ) {
            error_log( "SharePoint Connect: Permissions modifiées pour le fichier : $file_path" );
            return true;
        } else {
            error_log( "SharePoint Connect: Impossible de modifier les permissions du fichier : $file_path" );
            return false;
        }
    }
}

// Initialiser le plugin
SharePoint_Connect::get_instance();

<?php
/*
Plugin Name: SharePoint Connect
Plugin URI: https://votre-site.com/sharepoint-connect
Description: Connecte Formidable Forms à SharePoint via FastAPI.
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
        $this->settings = get_option( 'spc_settings', $this->default_settings() );

        // Admin menu
        add_action( 'admin_menu', array( $this, 'add_admin_menu' ) );

        // Register settings
        add_action( 'admin_init', array( $this, 'register_settings' ) );

        // Enqueue admin styles
        add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_admin_styles' ) );

        // Hook into Formidable Forms
        add_action( 'frm_after_create_entry', array( $this, 'send_files_to_fastapi' ), 10, 2 );

        // Load plugin textdomain for translations
        add_action( 'plugins_loaded', array( $this, 'load_textdomain' ) );
    }

    private function default_settings() {
        return array(
            'form_id'             => '',
            'fastapi_url'        => '',
            'api_token'          => '',
            'field_mappings'     => array(
                'name'          => '',
                'date_of_birth' => '',
                'email'         => '',
                'files'         => '',
            ),
            'doc_id_key'          => '', // Nouveau champ ajouté
            'doc_type_key'        => '', // Nouveau champ ajouté
            'relative_file_path' => 'wp-content/documents-private/',
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

        // Form ID
        add_settings_field(
            'form_id',
            __( 'ID du Formulaire', 'sharepoint-connect' ),
            array( $this, 'form_id_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // FastAPI URL
        add_settings_field(
            'fastapi_url',
            __( 'URL de FastAPI', 'sharepoint-connect' ),
            array( $this, 'fastapi_url_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // API Token
        add_settings_field(
            'api_token',
            __( 'Token API', 'sharepoint-connect' ),
            array( $this, 'api_token_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Field Mappings
        add_settings_field(
            'field_mappings',
            __( 'Mappages des Champs', 'sharepoint-connect' ),
            array( $this, 'field_mappings_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Doc ID Key (Nouveau champ)
        add_settings_field(
            'doc_id_key',
            __( 'Clé ID du Document', 'sharepoint-connect' ),
            array( $this, 'doc_id_key_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Doc Type Key (Nouveau champ)
        add_settings_field(
            'doc_type_key',
            __( 'Clé Type du Document', 'sharepoint-connect' ),
            array( $this, 'doc_type_key_callback' ),
            'sharepoint-connect',
            'spc_main_section'
        );

        // Relative File Path
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
        $sanitized['fastapi_url'] = esc_url_raw( $input['fastapi_url'] );
        $sanitized['api_token'] = sanitize_text_field( $input['api_token'] );

        $sanitized['field_mappings'] = array(
            'name'          => sanitize_text_field( $input['field_mappings']['name'] ),
            'date_of_birth' => sanitize_text_field( $input['field_mappings']['date_of_birth'] ),
            'email'         => sanitize_text_field( $input['field_mappings']['email'] ),
            'files'         => sanitize_text_field( $input['field_mappings']['files'] ),
        );

        $sanitized['doc_id_key'] = sanitize_text_field( $input['doc_id_key'] ); // Sanitisation du nouveau champ
        $sanitized['doc_type_key'] = sanitize_text_field( $input['doc_type_key'] ); // Sanitisation du nouveau champ

        $sanitized['relative_file_path'] = sanitize_text_field( $input['relative_file_path'] );

        // Logs de débogage
        error_log( "SharePoint Connect: 'name' field mapping sanitized value: " . $sanitized['field_mappings']['name'] );
        error_log( "SharePoint Connect: 'date_of_birth' field mapping sanitized value: " . $sanitized['field_mappings']['date_of_birth'] );
        error_log( "SharePoint Connect: 'email' field mapping sanitized value: " . $sanitized['field_mappings']['email'] );
        error_log( "SharePoint Connect: 'files' field mapping sanitized value: " . $sanitized['field_mappings']['files'] );
        error_log( "SharePoint Connect: 'doc_id_key' sanitized value: " . $sanitized['doc_id_key'] );
        error_log( "SharePoint Connect: 'doc_type_key' sanitized value: " . $sanitized['doc_type_key'] );

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

    // Callbacks for settings fields
    public function form_id_callback() {
        printf(
            '<input type="number" id="form_id" name="spc_settings[form_id]" value="%s" />',
            esc_attr( $this->settings['form_id'] )
        );
    }

    public function fastapi_url_callback() {
        printf(
            '<input type="url" id="fastapi_url" name="spc_settings[fastapi_url]" value="%s" size="50" />',
            esc_attr( $this->settings['fastapi_url'] )
        );
    }

    public function api_token_callback() {
        printf(
            '<input type="text" id="api_token" name="spc_settings[api_token]" value="%s" size="50" />',
            esc_attr( $this->settings['api_token'] )
        );
    }

    public function field_mappings_callback() {
        $mappings = $this->settings['field_mappings'];
        ?>
        <table class="form-table">
            <tr>
                <th><?php _e( 'Champ', 'sharepoint-connect' ); ?></th>
                <th><?php _e( 'ID du Champ Formidable', 'sharepoint-connect' ); ?></th>
            </tr>
            <tr>
                <td><?php _e( 'Nom', 'sharepoint-connect' ); ?></td>
                <td><input type="text" name="spc_settings[field_mappings][name]" value="<?php echo esc_attr( $mappings['name'] ); ?>" /></td>
            </tr>
            <tr>
                <td><?php _e( 'Date de Naissance', 'sharepoint-connect' ); ?></td>
                <td><input type="text" name="spc_settings[field_mappings][date_of_birth]" value="<?php echo esc_attr( $mappings['date_of_birth'] ); ?>" /></td>
            </tr>
            <tr>
                <td><?php _e( 'Email', 'sharepoint-connect' ); ?></td>
                <td><input type="text" name="spc_settings[field_mappings][email]" value="<?php echo esc_attr( $mappings['email'] ); ?>" /></td>
            </tr>
            <tr>
                <td><?php _e( 'Fichiers', 'sharepoint-connect' ); ?></td>
                <td><input type="text" name="spc_settings[field_mappings][files]" value="<?php echo esc_attr( $mappings['files'] ); ?>" /></td>
            </tr>
        </table>
        <p class="description"><?php _e( 'Entrez les IDs des champs de votre formulaire Formidable Forms.', 'sharepoint-connect' ); ?></p>
        <?php
    }

    // Callback pour Doc ID Key
    public function doc_id_key_callback() {
        printf(
            '<input type="text" id="doc_id_key" name="spc_settings[doc_id_key]" value="%s" size="50" />',
            esc_attr( $this->settings['doc_id_key'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé pour l\'ID du document.', 'sharepoint-connect' ) . '</p>';
    }

    // Callback pour Doc Type Key
    public function doc_type_key_callback() {
        printf(
            '<input type="text" id="doc_type_key" name="spc_settings[doc_type_key]" value="%s" size="50" />',
            esc_attr( $this->settings['doc_type_key'] )
        );
        echo '<p class="description">' . __( 'Entrez la clé pour le type de document.', 'sharepoint-connect' ) . '</p>';
    }

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
     * Fonction principale pour envoyer les fichiers à FastAPI
     */
    public function send_files_to_fastapi( $entry_id, $form_id ) {
        if ( $form_id != $this->settings['form_id'] ) { // Vérifie le Form ID
            return;
        }

        // Vérifie si $_POST['item_meta'] est défini
        if ( ! isset( $_POST['item_meta'] ) || ! is_array( $_POST['item_meta'] ) ) {
            // Correction de la ligne d'erreur
            error_log( "SharePoint Connect: 'item_meta' n'est pas défini ou n'est pas un tableau pour l'entrée ID $entry_id." );
            return;
        }

        // Récupère les champs mappés depuis les paramètres
        $name_field_id           = intval( $this->settings['field_mappings']['name'] );
        $date_of_birth_field_id  = intval( $this->settings['field_mappings']['date_of_birth'] );
        $email_field_id          = intval( $this->settings['field_mappings']['email'] );
        $files_field_id          = intval( $this->settings['field_mappings']['files'] );
        $doc_id_key              = sanitize_text_field( $this->settings['doc_id_key'] );
        $doc_type_key            = sanitize_text_field( $this->settings['doc_type_key'] );

        // Récupère les données de l'entrée via $_POST['item_meta']
        $name          = isset( $_POST['item_meta'][ $name_field_id ] ) ? sanitize_text_field( $_POST['item_meta'][ $name_field_id ] ) : '';
        $date_of_birth = isset( $_POST['item_meta'][ $date_of_birth_field_id ] ) ? sanitize_text_field( $_POST['item_meta'][ $date_of_birth_field_id ] ) : '';
        $email         = isset( $_POST['item_meta'][ $email_field_id ] ) ? sanitize_email( $_POST['item_meta'][ $email_field_id ] ) : '';
        $files         = isset( $_POST['item_meta'][ $files_field_id ] ) ? $_POST['item_meta'][ $files_field_id ] : array();

        // Logs de débogage
        error_log( "SharePoint Connect: Récupération des champs pour l'entrée ID $entry_id." );
        error_log( "SharePoint Connect: Nom: $name, Date de Naissance: $date_of_birth, Email: $email" );

        // Vérifie que les fichiers existent et sont sous forme de tableau
        if ( empty( $files ) || ! is_array( $files ) ) {
            error_log( "SharePoint Connect: Aucun fichier trouvé pour l'entrée ID $entry_id." );
            return;
        }

        var_dump( $files );

        die();
        
        $files_and_docs = array();

        foreach ( $files as $file ) {
            if ( isset( $file[$doc_id_key ] ) && isset( $file[$doc_type_key] ) ) {
                $file_id  = intval( $file[$doc_id_key] ); // ID du fichier
                $doc_type = sanitize_text_field( $file[$doc_type_key] ); // Type de document

                $file_path = $this->resolve_file_path( $file_id );
                if ( $file_path && file_exists( $file_path ) ) {
                    $files_and_docs[] = array(
                        'file' => $file_path,
                        'type' => $doc_type
                    );
                } else {
                    error_log( "SharePoint Connect: Fichier introuvable ou non lisible pour l'ID $file_id." );
                }
            }
        }

        if ( empty( $files_and_docs ) ) {
            error_log( "SharePoint Connect: Aucun fichier valide trouvé pour l'entrée ID $entry_id." );
            return;
        }

        // Prépare les données POST pour FastAPI
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
        curl_setopt( $ch, CURLOPT_URL, $this->settings['fastapi_url'] );
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
            error_log( "SharePoint Connect: FastAPI responded with status code $http_code. Response: $response" );
        }
    }

    /**
     * Résout le chemin du fichier en fonction de l'ID
     */
    private function resolve_file_path( $file_id ) {
        $relative_path      = trailingslashit( $this->settings['relative_file_path'] );
        $file_path_original = get_attached_file( $file_id );

        if ( ! $file_path_original ) {
            error_log( "SharePoint Connect: Impossible de récupérer le chemin du fichier pour l'ID $file_id." );
            return false;
        }

        $file_name = basename( $file_path_original );

        // Construire le chemin relatif complet
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

?>

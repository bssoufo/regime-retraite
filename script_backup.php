<?php
/**
 * Theme functions and definitions
 *
 * @package HelloElementor
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

define( 'HELLO_ELEMENTOR_VERSION', '2.5.0' );

if ( ! isset( $content_width ) ) {
	$content_width = 800; // Pixels.
}

if ( ! function_exists( 'hello_elementor_setup' ) ) {
	/**
	 * Set up theme support.
	 *
	 * @return void
	 */
	function hello_elementor_setup() {
		if ( is_admin() ) {
			hello_maybe_update_theme_version_in_db();
		}

		$hook_result = apply_filters_deprecated( 'elementor_hello_theme_load_textdomain', [ true ], '2.0', 'hello_elementor_load_textdomain' );
		if ( apply_filters( 'hello_elementor_load_textdomain', $hook_result ) ) {
			load_theme_textdomain( 'hello-elementor', get_template_directory() . '/languages' );
		}

		$hook_result = apply_filters_deprecated( 'elementor_hello_theme_register_menus', [ true ], '2.0', 'hello_elementor_register_menus' );
		if ( apply_filters( 'hello_elementor_register_menus', $hook_result ) ) {
			register_nav_menus( [ 'menu-1' => __( 'Header', 'hello-elementor' ) ] );
			register_nav_menus( [ 'menu-2' => __( 'Footer', 'hello-elementor' ) ] );
		}

		$hook_result = apply_filters_deprecated( 'elementor_hello_theme_add_theme_support', [ true ], '2.0', 'hello_elementor_add_theme_support' );
		if ( apply_filters( 'hello_elementor_add_theme_support', $hook_result ) ) {
			add_theme_support( 'post-thumbnails' );
			add_theme_support( 'automatic-feed-links' );
			add_theme_support( 'title-tag' );
			add_theme_support(
				'html5',
				[
					'search-form',
					'comment-form',
					'comment-list',
					'gallery',
					'caption',
				]
			);
			add_theme_support(
				'custom-logo',
				[
					'height'      => 100,
					'width'       => 350,
					'flex-height' => true,
					'flex-width'  => true,
				]
			);

			/*
			 * Editor Style.
			 */
			add_editor_style( 'classic-editor.css' );

			/*
			 * Gutenberg wide images.
			 */
			add_theme_support( 'align-wide' );

			/*
			 * WooCommerce.
			 */
			$hook_result = apply_filters_deprecated( 'elementor_hello_theme_add_woocommerce_support', [ true ], '2.0', 'hello_elementor_add_woocommerce_support' );
			if ( apply_filters( 'hello_elementor_add_woocommerce_support', $hook_result ) ) {
				// WooCommerce in general.
				add_theme_support( 'woocommerce' );
				// Enabling WooCommerce product gallery features (are off by default since WC 3.0.0).
				// zoom.
				add_theme_support( 'wc-product-gallery-zoom' );
				// lightbox.
				add_theme_support( 'wc-product-gallery-lightbox' );
				// swipe.
				add_theme_support( 'wc-product-gallery-slider' );
			}
		}
	}
}
add_action( 'after_setup_theme', 'hello_elementor_setup' );

function hello_maybe_update_theme_version_in_db() {
	$theme_version_option_name = 'hello_theme_version';
	// The theme version saved in the database.
	$hello_theme_db_version = get_option( $theme_version_option_name );

	// If the 'hello_theme_version' option does not exist in the DB, or the version needs to be updated, do the update.
	if ( ! $hello_theme_db_version || version_compare( $hello_theme_db_version, HELLO_ELEMENTOR_VERSION, '<' ) ) {
		update_option( $theme_version_option_name, HELLO_ELEMENTOR_VERSION );
	}
}

if ( ! function_exists( 'hello_elementor_scripts_styles' ) ) {
	/**
	 * Theme Scripts & Styles.
	 *
	 * @return void
	 */
	function hello_elementor_scripts_styles() {
		$enqueue_basic_style = apply_filters_deprecated( 'elementor_hello_theme_enqueue_style', [ true ], '2.0', 'hello_elementor_enqueue_style' );
		$min_suffix          = defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ? '' : '.min';

		if ( apply_filters( 'hello_elementor_enqueue_style', $enqueue_basic_style ) ) {
			wp_enqueue_style(
				'hello-elementor',
				get_template_directory_uri() . '/style' . $min_suffix . '.css',
				[],
				HELLO_ELEMENTOR_VERSION
			);
		}

		if ( apply_filters( 'hello_elementor_enqueue_theme_style', true ) ) {
			wp_enqueue_style(
				'hello-elementor-theme-style',
				get_template_directory_uri() . '/theme' . $min_suffix . '.css',
				[],
				HELLO_ELEMENTOR_VERSION
			);
		}
	}
}
add_action( 'wp_enqueue_scripts', 'hello_elementor_scripts_styles' );

if ( ! function_exists( 'hello_elementor_register_elementor_locations' ) ) {
	/**
	 * Register Elementor Locations.
	 *
	 * @param ElementorPro\Modules\ThemeBuilder\Classes\Locations_Manager $elementor_theme_manager theme manager.
	 *
	 * @return void
	 */
	function hello_elementor_register_elementor_locations( $elementor_theme_manager ) {
		$hook_result = apply_filters_deprecated( 'elementor_hello_theme_register_elementor_locations', [ true ], '2.0', 'hello_elementor_register_elementor_locations' );
		if ( apply_filters( 'hello_elementor_register_elementor_locations', $hook_result ) ) {
			$elementor_theme_manager->register_all_core_location();
		}
	}
}
add_action( 'elementor/theme/register_locations', 'hello_elementor_register_elementor_locations' );

if ( ! function_exists( 'hello_elementor_content_width' ) ) {
	/**
	 * Set default content width.
	 *
	 * @return void
	 */
	function hello_elementor_content_width() {
		$GLOBALS['content_width'] = apply_filters( 'hello_elementor_content_width', 800 );
	}
}
add_action( 'after_setup_theme', 'hello_elementor_content_width', 0 );

if ( is_admin() ) {
	require get_template_directory() . '/includes/admin-functions.php';
}

/**
 * If Elementor is installed and active, we can load the Elementor-specific Settings & Features
*/

// Allow active/inactive via the Experiments
require get_template_directory() . '/includes/elementor-functions.php';

/**
 * Include customizer registration functions
*/
function hello_register_customizer_functions() {
	if ( hello_header_footer_experiment_active() && is_customize_preview() ) {
		require get_template_directory() . '/includes/customizer-functions.php';
	}
}
add_action( 'init', 'hello_register_customizer_functions' );

if ( ! function_exists( 'hello_elementor_check_hide_title' ) ) {
	/**
	 * Check hide title.
	 *
	 * @param bool $val default value.
	 *
	 * @return bool
	 */
	function hello_elementor_check_hide_title( $val ) {
		if ( defined( 'ELEMENTOR_VERSION' ) ) {
			$current_doc = Elementor\Plugin::instance()->documents->get( get_the_ID() );
			if ( $current_doc && 'yes' === $current_doc->get_settings( 'hide_title' ) ) {
				$val = false;
			}
		}
		return $val;
	}
}
add_filter( 'hello_elementor_page_title', 'hello_elementor_check_hide_title' );

/**
 * Wrapper function to deal with backwards compatibility.
 */
if ( ! function_exists( 'hello_elementor_body_open' ) ) {
	function hello_elementor_body_open() {
		if ( function_exists( 'wp_body_open' ) ) {
			wp_body_open();
		} else {
			do_action( 'wp_body_open' );
		}
	}
}
add_filter( 'wp_lazy_loading_enabled', '__return_false' );



add_filter('frm_upload_folder', 'frm_custom_upload');
function frm_custom_upload($folder){
	$folder = '../../wp-content/documents-private/';
    return $folder;
}







// Bruno
// 
// 
/**
 * Intercept Formidable Form email and send a copy to bssoufo@gmail.com.
 *
 * @param array $args    The arguments passed to the wp_mail function.
 * @param array $entry   The entry data from Formidable.
 * @param array $form_id The ID of the Formidable Form.
 */



/**
 * Intercept Formidable submission, send custom email (with files), then prevent saving.
 */
//add_action( 'frm_entries_before_create', 'my_custom_formidable_email_no_save', 1, 2 );
function my_custom_formidable_email_no_save( $values, $form ) {

    // 1. Specify which form(s) you want to target
    $target_form_ids = array( 4 ); // e.g. form ID = 4
    if ( ! in_array( (int) $form->id, $target_form_ids, true ) ) {
        return; // Do nothing if it's not our target form
    }

	var_dump($values);
	echo '===================================';
	var_dump($form);
	echo '===================================';
	var_dump($_POST);
	 $field_ids = array( 32 );
	$file_ids = array_filter( (array) $_POST['item_meta'][35][0][ $field_id ], 'is_numeric' );

	echo '===================================';
	var_dump($_POST['item_meta'][35][0][32]);
	foreach ( $file_ids as $file_id ) {
				$file_id = absint( $file_id );
				$old_source = get_attached_file( $file_id );
				$file_name = basename( $old_source );
					echo $file_name;
			}


	die();
    // 2. Remove Formidable's default save + notification actions
    //    This ensures the entry won't be stored, and Formidable's own emails won't be sent.
    remove_action( 'frm_entries_before_create', 'FrmFormActionsController::trigger_actions', 20 );
    remove_action( 'frm_entries_before_create', 'FrmEntry::create', 30 );

    /**
     * 3. Build a custom email message with all submitted data.
     *    - $values['item_meta'] holds the field_id => user_input
     *    - $values['attached_files'] holds any uploaded files
     */
    $message  = "A new submission from Form #{$form->id} was intercepted:\n\n";
    
    // Append all text-based fields
    if ( isset( $values['item_meta'] ) && is_array( $values['item_meta'] ) ) {
        foreach ( $values['item_meta'] as $field_id => $user_input ) {
            // Adjust formatting/field labels to your liking
            $message .= "Field {$field_id}: " . print_r( $user_input, true ) . "\n";
        }
    }

    // 4. Prepare file attachments (if any)
    $attachments = array();
    if ( ! empty( $values['attached_files'] ) && is_array( $values['attached_files'] ) ) {
        foreach ( $values['attached_files'] as $field_id => $file_data ) {

            // $file_data can be an array of file info if multiple files were attached
            // Example structure: [ [ 'file_path' => '...', 'url' => '...', 'name' => '...' ], ... ]
            if ( is_array( $file_data ) ) {
                foreach ( $file_data as $single_file ) {
                    if ( ! empty( $single_file['file_path'] ) && file_exists( $single_file['file_path'] ) ) {
                        $attachments[] = $single_file['file_path'];
                        // You could also mention in the message
                        $message .= "\nAttached file for Field {$field_id}: " . $single_file['name'];
                    }
                }
            }
        }
    }

    // 5. Optionally add a custom footer
    $message .= "\n\n--- End of Intercepted Submission ---";

    // 6. Send your custom email (include attachments if desired)
    $to      = 'bssoufo@gmail.com';
    $subject = 'Intercepted Form Submission (Form ' . $form->id . ')';
    $headers = array( 'Content-Type: text/plain; charset=UTF-8' ); // or text/html if needed

    $sent = wp_mail( $to, $subject, $message, $headers, $attachments );
    if ( $sent ) {
        error_log( "Custom email sent successfully for Form #{$form->id}." );
    } else {
        error_log( "Failed to send custom email for Form #{$form->id}!" );
    }

    // 7. Since we removed the default actions, Formidable won't save or send its own emails.
    //    The user will still see the default success message unless you customize that too.
}



add_action('frm_after_create_entry', 'send_files_and_documents_via_email', 10, 2);
add_action('frm_after_create_entry', 'send_files_to_fastapi', 10, 2);
function send_files_and_documents_via_email($entry_id, $form_id) {
    if ($form_id != 4) { // Vérifiez que l'ID du formulaire est bien 4
        return;
    }

    // Vérifiez si le champ 35 existe dans $_POST
    if (isset($_POST['item_meta'][35]) && is_array($_POST['item_meta'][35])) {
	
        $files_and_docs = []; // Stocker les fichiers et leurs types
        $attachments = [];   // Stocker les chemins des fichiers pour les pièces jointes

        // Parcourir chaque ligne du champ 35
        foreach ($_POST['item_meta'][35] as $line) {
            if (isset($line[32]) && isset($line[34])) {
                $file_id = $line[32]; // ID du fichier
                $doc_type = $line[34]; // Type de document

                // Récupérer le chemin absolu corrigé du fichier attaché
                $file_path = resolve_file_path($file_id);
                if ($file_path && file_exists($file_path)) {
                    // Ajouter les données au tableau
                    $files_and_docs[] = [
                        'file' => $file_path,
                        'type' => $doc_type
                    ];
                    $attachments[] = $file_path; // Ajouter à la liste des pièces jointes
                }
            }
        }
		 
		//die();

        // Composer le contenu de l'email
        $email_subject = "Documents soumis via le formulaire";
        $email_body = "Voici les fichiers soumis avec leurs types de documents :\n\n";
        foreach ($files_and_docs as $file_doc) {
            $email_body .= "Type de document : {$file_doc['type']}\n";
            $email_body .= "Chemin du fichier : {$file_doc['file']}\n\n";
        }

        // Envoyer l'email
        $to = 'bssoufo@gmail.com'; // Adresse email du destinataire
        $headers = ['Content-Type: text/html; charset=UTF-8'];
        wp_mail($to, $email_subject, nl2br($email_body), $headers, $attachments);
    }
}




function send_files_to_fastapi($entry_id, $form_id) {
    if ($form_id != 4) { // Ensure the form ID is 4
        return;
    }

    // Define the FastAPI endpoint URL
    $fastapi_url = 'https://5fa6-70-82-91-207.ngrok-free.app/uploadfiles/'; // Update if different

    // Define the API token
    $api_token = '649b5b43d958a45bf84842f1ba59571dac8e9216442a941f0dc6eee9f558de79';

    // Extract form fields: Adjust the indices based on your form's structure
    $name = isset($_POST['item_meta'][27]) ? sanitize_text_field($_POST['item_meta'][27]) : '';
    $date_of_birth = isset($_POST['item_meta'][28]) ? sanitize_text_field($_POST['item_meta'][28]) : '';
    $email = isset($_POST['item_meta'][29]) ? sanitize_email($_POST['item_meta'][29]) : '';

    // Check if the files field exists and is an array
    if (isset($_POST['item_meta'][35]) && is_array($_POST['item_meta'][35])) {

        $files_and_docs = []; // To store files and their types

        foreach ($_POST['item_meta'][35] as $line) {
            if (isset($line[32]) && isset($line[34])) {
                $file_id = $line[32]; // File ID
                $doc_type = sanitize_text_field($line[34]); // Document type

                $file_path = resolve_file_path($file_id);
                if ($file_path && file_exists($file_path)) {
                    $files_and_docs[] = [
                        'file' => $file_path,
                        'type' => $doc_type
                    ];
                }
            }
        }

        // Prepare POST fields for FastAPI
        $post_fields = [
            'name' => $name,
            'date_of_birth' => $date_of_birth,
            'email' => $email,
        ];

        foreach ($files_and_docs as $index => $file_doc) {
            $file_path = $file_doc['file'];
            $doc_type = $file_doc['type'];

            if (file_exists($file_path)) {
                $post_fields["file_$index"] = new CURLFile($file_path);
                $post_fields["description_$index"] = $doc_type;
            }
        }

        // Initialize cURL
        $ch = curl_init();

        // Set cURL options
        curl_setopt($ch, CURLOPT_URL, $fastapi_url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post_fields);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: multipart/form-data',
            "X-API-Token: $api_token" // Add the API token header
        ]);

        // Execute the POST request
        $response = curl_exec($ch);

        // Check for cURL errors
        if ($response === false) {
            $error = curl_error($ch);
            error_log("cURL Error: $error");
            curl_close($ch);
            return;
        }

        // Get HTTP response code
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        // Handle the response
        if ($http_code >= 200 && $http_code < 300) {
            // Success - Optionally process the response
        } else {
            // Log the error
            error_log("FastAPI responded with status code $http_code. Response: $response");
        }
    }
}





function frm_filesystem_prepared() {
	if ( ! is_admin() || ! function_exists( 'get_filesystem_method' ) ) {
		include_once(ABSPATH . 'wp-admin/includes/file.php');
	}

	$access_type = get_filesystem_method();
	if ( $access_type === 'direct' ) {
		$creds = request_filesystem_credentials( site_url() . '/wp-admin/', '', false, false, array() );
	}

	return ( ! empty( $creds ) && WP_Filesystem( $creds ) );
}

// Fonction pour résoudre correctement le chemin du fichier
function resolve_file_path2($file_id) {
    $file_path = get_attached_file($file_id);
		var_dump($file_path);
	var_dump(is_readable($file_path));
    // Si le chemin contient ../../, le convertir en chemin absolu
    if (strpos($file_path, '../../') !== false) {
        $file_path = realpath($file_path);
    }
	var_dump($file_path);
	var_dump(is_readable($file_path));
    // Vérifiez que le fichier existe et est accessible
    return (file_exists($file_path) && is_readable($file_path)) ? $file_path : false;
}

function resolve_file_path($file_id) {
    $relative_path = 'wp-content/documents-private/'; // Chemin relatif vers le répertoire
    $file_name = basename(get_attached_file($file_id)); // Récupère le nom du fichier uniquement

    // Construire le chemin relatif complet
    $file_path = ABSPATH . $relative_path . $file_name;
	make_file_readable($file_path);
			var_dump($file_path);
	var_dump(is_readable($file_path));
    // Vérifier si le fichier existe et est lisible
    if (file_exists($file_path)) {
        if (is_readable($file_path)) {
            error_log("Le fichier est lisible : $file_path");
            return $file_path;
        } else {
            error_log("Le fichier n'est pas lisible : $file_path");
        }
    } else {
        error_log("Fichier introuvable : $file_path");
    }

    return false;
}



// Fonction pour télécharger un fichier sur le serveur temporairement
function download_file_to_server($file_url) {
    $upload_dir = wp_upload_dir();
    $temp_path = $upload_dir['basedir'] . '/temp_' . basename($file_url);
	
    // Télécharger le fichier
    $response = wp_remote_get($file_url);
    if (is_wp_error($response)) {
        return false;
    }

    $file_data = wp_remote_retrieve_body($response);
    if (file_put_contents($temp_path, $file_data)) {
        return $temp_path;
    }

    return false;
}


function make_file_readable($file_path) {
    // Vérifiez si le fichier existe
    if (!file_exists($file_path)) {
        error_log("Fichier introuvable : $file_path");
        return false;
    }

    // Modifier les permissions pour rendre le fichier lisible
    if (chmod($file_path, 0644)) {
        error_log("Permissions modifiées pour le fichier : $file_path");
        return true;
    } else {
        error_log("Impossible de modifier les permissions du fichier : $file_path");
        return false;
    }
}

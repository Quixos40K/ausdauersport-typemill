<?php

namespace Plugins\jsonldmeta;

use Typemill\Plugin;

/**
 * Adds an editable JSON-LD field to Typemill's Meta tab and renders valid
 * JSON-LD in the frontend through assets.renderMeta().
 */
class jsonldmeta extends Plugin
{
    /** @var string|null */
    private $jsonLd = null;

    public static function getSubscribedEvents()
    {
        return [
            'onMetaLoaded' => ['onMetaLoaded', 0],
            'onPageReady' => ['onPageReady', 0],
        ];
    }

    /**
     * Read the page-specific value from meta.json_ld.
     */
    public function onMetaLoaded($meta)
    {
        $metadata = $meta->getData();
        $jsonLd = $metadata['meta']['json_ld'] ?? null;

        if (!is_string($jsonLd)) {
            return;
        }

        $jsonLd = trim($jsonLd);

        if ($jsonLd === '') {
            return;
        }

        json_decode($jsonLd, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            return;
        }

        // Prevent an embedded closing script tag from ending the element early.
        $this->jsonLd = str_ireplace('</script', '<\/script', $jsonLd);
    }

    /**
     * Add the JSON-LD script to the existing assets.renderMeta() output.
     */
    public function onPageReady($pageData)
    {
        if ($this->jsonLd === null) {
            return;
        }

        $assets = $this->container->get('assets');
        $assets->addMeta(
            'jsonldmeta',
            '<script type="application/ld+json">' . $this->jsonLd . '</script>'
        );
    }
}

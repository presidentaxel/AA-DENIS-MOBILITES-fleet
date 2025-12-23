-- Script SQL pour insérer des cookies de test dans heetch_session_cookies
-- Remplace les valeurs suivantes :
-- - :org_id : ton org_id (par défaut 'default_org')
-- - :phone_number : ton numéro de téléphone (ex: '+33743617110')
-- - :expires_at : date d'expiration des cookies (par défaut 24h après maintenant)

INSERT INTO heetch_session_cookies (
    id,
    org_id,
    phone_number,
    cookies,
    expires_at,
    invalid_at,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'default_org',  -- Remplace par ton org_id si différent
    '+33743617110',  -- Remplace par ton numéro de téléphone
    '[
        {
            "name": "AEC",
            "value": "AaJma5t-cCFOaqt6sl97gny1gR6HitVWBVNFvUKMZSzkuh2vRCDQoUBsSyA",
            "domain": ".google.com",
            "path": "/",
            "expires": 1715444740,
            "httpOnly": true,
            "secure": true,
            "sameSite": "Lax"
        },
        {
            "name": "ajs_anonymous_id",
            "value": "a916fcbd-36e4-4f73-9100-6969d1a73908",
            "domain": ".heetch.com",
            "path": "/",
            "expires": 1734957719,
            "httpOnly": false,
            "secure": false,
            "sameSite": "Lax"
        },
        {
            "name": "APISID",
            "value": "LxLHvJOGQqPPWPnk/AwgmHgROe7JNbntuL",
            "domain": ".google.fr",
            "path": "/",
            "expires": 1736262343,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "APISID",
            "value": "LxLHvJOGQqPPWPnk/AwgmHgROe7JNbntuL",
            "domain": ".google.com",
            "path": "/",
            "expires": 1736262342,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "ar_debug",
            "value": "1",
            "domain": ".doubleclick.net",
            "path": "/",
            "expires": 1719073673,
            "httpOnly": true,
            "secure": true,
            "sameSite": "None"
        },
        {
            "name": "axeptio_all_vendors",
            "value": "%2Cdouble_click%2Cgoogle_analytics%2Clinkedin%2CGoogle%20Conversion%20Linker%2Chubspot%2CDouble_Click%2CLinkedin%2C",
            "domain": "auth.heetch.com",
            "path": "/",
            "expires": 1718476031,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "axeptio_authorized_vendors",
            "value": "%2Cdouble_click%2Cgoogle_analytics%2Clinkedin%2CGoogle%20Conversion%20Linker%2Chubspot%2CDouble_Click%2CLinkedin%2C",
            "domain": "auth.heetch.com",
            "path": "/",
            "expires": 1718476031,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "axeptio_cookies",
            "value": "{%22$$token%22:%22r0KP93QUraYciOYIqtwkYVQu9I%22%2C%22$$date%22:%222025-12-17T13:07:11.719Z%22%2C%22$$cookiesVersion%22:{%22name%22:%22-fr%22%2C%22identifier%22:%225fc66899f818424c2a689c82%22}%2C%22double_click%22:true%2C%22google_analytics%22:true%2C%22linkedin%22:true%2C%22Google%20Conversion%20Linker%22:true%2C%22hubspot%22:true%2C%22Double_Click%22:true%2C%22Linkedin%22:true%2C%22$$googleConsentMode%22:{%22analytics_storage%22:%22granted%22%2C%22ad_storage%22:%22granted%22%2C%22ad_user_data%22:%22granted%22%2C%22ad_personalization%22:%22granted%22%2C%22version%22:2}%2C%22$$scope%22:%22persistent%22%2C%22$$duration%22:180%2C%22$$completed%22:true}",
            "domain": "auth.heetch.com",
            "path": "/",
            "expires": 1718476031,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "device_id",
            "value": "5914648b-d4a9-443d-b638-7746eff47ab7",
            "domain": ".heetch.com",
            "path": "/",
            "expires": 1734479180,
            "httpOnly": true,
            "secure": false,
            "sameSite": "Lax"
        },
        {
            "name": "DSID",
            "value": "AEhM4Meayan86XG9hx0YizrruIPjwo0SjaYeKzvmTTddp2KsvoofMXPjH3-SGxkDWzXSVhls-IbZQn60-DHSPM250gC4pUVuZbVtZGLZR2goJvd9dB-ofd_REp6qJ-v_b0dBUWkkIZJF8IU6rx8waeFkD33QFAHrpjZvo2_IatOSD0RDcJfD8MhznPgcuNgwUAJe9dYK0qSKB4TwjlxJnEn-aWibMxKISkiR_7n-XhgQdUvRAuEBJ2FY6btgvY_3qSfYvingUJC2_ly0F7l5j80poAPxEgMd1AYZ0m4h27TwSUElN1dFXAU",
            "domain": ".doubleclick.net",
            "path": "/",
            "expires": 1733270400,
            "httpOnly": true,
            "secure": true,
            "sameSite": "None"
        },
        {
            "name": "HSID",
            "value": "ApsnKqbt9aerEcd17",
            "domain": ".google.fr",
            "path": "/",
            "expires": 1736262343,
            "httpOnly": true,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "HSID",
            "value": "A2xveR2YmkJpJZAqW",
            "domain": ".google.com",
            "path": "/",
            "expires": 1736262342,
            "httpOnly": true,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "hubspotutk",
            "value": "ffe2be1aea9907b2cc227167b422b06c",
            "domain": ".heetch.com",
            "path": "/",
            "expires": 1718819142,
            "httpOnly": false,
            "secure": false,
            "sameSite": "Lax"
        },
        {
            "name": "IDE",
            "value": "AHWqTUlfpyf2tYJ4KJWnOkF5xMBlP-1AEBxx8q2ieVqQsxzvXsS85yzfRe2Uo5yHhUw",
            "domain": ".doubleclick.net",
            "path": "/",
            "expires": 1733594074,
            "httpOnly": true,
            "secure": true,
            "sameSite": "None"
        },
        {
            "name": "NID",
            "value": "526=q-o1hWe6C1u7J18IkVwmhKzKLI1bNKrkAK6NOvZr-KARljOthU_3SFT6qTtCHyzBTa1ygsHi03L-zwz1rUMMShiyCaMlLOAGvkEsKfadm2EDkufTQGp-jmZOwyVZeKR3aAoEP6ukDa0v4vUcO01tNEjOq1z7xFdLtf1NYFAPHHlxk4SthFRQt4JB0PnLji6SlZQ89UQRxKv5ZEB9b-3pFqlHdLdBrMzJUdeHDaoRnjZblyCfGG2llLYTW2hVujUIzGeAPlKo7AqefQI5lfM2xK8kNbTCm8O5gmQyMB5ussZrAV_BLCxbXHDghcehFip-moU2oC1LTuv6Rh4q68Qt3gb4GF7SHkXccQxMBLPW0yEJMlzvXMHpjrcdEQN_2AcSTPjgRnMqiZrCNYEkd2aatzJ8MyIUkOSh2jUw4s3P1QsOw1l3OdMv9P7UK0e_MqnNxsl8KAbhHUv1xQ58eVaCxn_UjRWbP7S94vnh4RUZuV6WnEfPWQ3exkJVVKoNh7CANsLlFT8BSCwkQGOQ5U8Q3gsG0BZQdsEwPyNAH56HcqSrsb8Uk4rGSusVEY2Df4KKgjBS7FtVIdd-ArO09hptyTVxtHfS-yiRukwaB_IImw2DylXUu_51OUoNZ3X7ljurobzweDhg6_Jo0HBh2sWX43htvBQywvW8s1b8ZHPHamuTsdca6USCmcmNZ7IhBYgGcWZYeDoDT8hDk2wKgbumaROg",
            "domain": ".google.fr",
            "path": "/",
            "expires": 1717520743,
            "httpOnly": true,
            "secure": true,
            "sameSite": "None"
        },
        {
            "name": "NID",
            "value": "527=IanaM_pEBoiBiWYqy98CjIC8Rlx8cr71b0ptZdVvMnqPeX4vwaVMiyI4ItGk4C379nCRMpzEAWnYrOwAh5He6qzT2cNNMy07w7S2Pajny443QdVHa7lwtQpBe1Oo4augo-Cfl6GI5Se9lwXhQDJNozIG_k_4WzK_zDf_67SXep16N0NzqMauqokiv82V95h5tIhBOal7U8UQSBg0xKRdMm9PufgnjEPM9k5DUvQvBHM7R7jZhqeeAWex_Cgh5BtVkiqIFLxCt0DsOKfb8pegNF5yN5bN3FKz1Alw6IT9X0yR3TkiBNKA9KAARSc-XXHxCCC-QTJ7IlHu4lTMUu2iC698TC98qjKtndNDTo-pw993swyltprJ5Kro2CkvfkdRn4ZFBrZ_VYvD-yqG9RjP9xdBk4YX5_lwybZsG0pj65Mf5nyrJaj7Qmt0aaXtWRvXhpbiCbLc1zBs9AuNvygZcROtF9cZvtnAy24u-N4yQBfje2Pwa5pDySseGRzmSwBsX4KYA3mjDRtwOprajkaVwi5ujO4NMkqG6LozFZfoFbcGL5bfvrje_f9vuebcdWagFfOaajTRfg7zrFvvxfSa0MX5FouTmjsWAEYUMJNPSERPR9wv9fw-Y7WIoxAWL9nCfV0TGuXBoMd7a0U1rtNT0XWb5EJy73M4HVOlQJifLmRTEJzgIBHk1mQEenW5hebzsXq2LQ",
            "domain": ".google.com",
            "path": "/",
            "expires": 1719147759,
            "httpOnly": true,
            "secure": true,
            "sameSite": "None"
        },
        {
            "name": "OTZ",
            "value": "8374505_52_52_123900_48_436380",
            "domain": "www.google.com",
            "path": "/",
            "expires": 1704204323,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "SAPISID",
            "value": "YAEyuNiX3jnjTKv4/AtIGXWXgiugJNOmRb",
            "domain": ".google.fr",
            "path": "/",
            "expires": 1736262343,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "SAPISID",
            "value": "YAEyuNiX3jnjTKv4/AtIGXWXgiugJNOmRb",
            "domain": ".google.com",
            "path": "/",
            "expires": 1736262342,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "SEARCH_SAMESITE",
            "value": "CgQItJ8B",
            "domain": ".google.com",
            "path": "/",
            "expires": 1715445939,
            "httpOnly": false,
            "secure": false,
            "sameSite": "Strict"
        },
        {
            "name": "SEARCH_SAMESITE",
            "value": "CgQItZ8B",
            "domain": ".google.fr",
            "path": "/",
            "expires": 1715617130,
            "httpOnly": false,
            "secure": false,
            "sameSite": "Strict"
        },
        {
            "name": "SID",
            "value": "g.a0004AigUE-XSi24p9D-UxsRq3Z4xO0F-_0-jh_-jZhvTiXWFrrTztX61U-08K4-BdiuY-CdMgACgYKAfgSARYSFQHGX2MiW433hfN4RdlkoUD8L44PwBoVAUF8yKpK5TliX1u7AQlGvrQxf9hW0076",
            "domain": ".google.com",
            "path": "/",
            "expires": 1736262342,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "SID",
            "value": "g.a0004AigUE-XSi24p9D-UxsRq3Z4xO0F-_0-jh_-jZhvTiXWFrrTztX61U-08K4-BdiuY-CdMgACgYKAfgSARYSFQHGX2MiW433hfN4RdlkoUD8L44PwBoVAUF8yKpK5TliX1u7AQlGvrQxf9hW0076",
            "domain": ".google.fr",
            "path": "/",
            "expires": 1736262343,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "SIDCC",
            "value": "AKEyXzW0cEKibzPww3Tmm6xJQI2ICwg7LW3cLQ9yJvF0TLKvcPzkoABPog61U05RHW_Lo7v7nwE",
            "domain": ".google.com",
            "path": "/",
            "expires": 1734892048,
            "httpOnly": false,
            "secure": false,
            "sameSite": null
        },
        {
            "name": "SSID",
            "value": "Anchglb6J7pD6GpLX",
            "domain": ".google.fr",
            "path": "/",
            "expires": 1736262343,
            "httpOnly": true,
            "secure": true,
            "sameSite": null
        },
        {
            "name": "SSID",
            "value": "AZHN67Egz16yHF5dT",
            "domain": ".google.com",
            "path": "/",
            "expires": 1736262342,
            "httpOnly": true,
            "secure": true,
            "sameSite": null
        }
    ]'::jsonb,
    NOW() + INTERVAL '24 hours',  -- expires_at: 24h après maintenant
    NULL,  -- invalid_at: NULL car cookies valides
    NOW(),  -- created_at
    NOW()   -- updated_at
)
ON CONFLICT (org_id, phone_number) 
DO UPDATE SET
    cookies = EXCLUDED.cookies,
    expires_at = EXCLUDED.expires_at,
    invalid_at = NULL,  -- Réinitialiser invalid_at car nouveaux cookies valides
    updated_at = NOW();


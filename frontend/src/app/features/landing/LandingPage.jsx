import { Typography } from "../../../../node_modules/@mui/material";
import { useTranslation } from "../../../../node_modules/react-i18next";


export default function StartPage() {
    const {t, i18n} = useTranslation();

    return (
        <>
            <Typography variant="h3" gutterBottom>
                {t("home.welcome")}
            </Typography>
        </>
    );
}
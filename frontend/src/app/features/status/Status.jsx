import Typography from "@mui/material/Typography";
import { Box } from "../../../../node_modules/@mui/material";
import { useTranslation } from "../../../../node_modules/react-i18next";


export default function Status(props) {
    const { t, i18n } = useTranslation();

    return (
        <Box className="status">
            <Typography variant="h3" gutterBottom>
                {t("area.status")}
            </Typography>
        </Box>
    )
}
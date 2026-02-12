document.addEventListener("DOMContentLoaded",()=>{
    const fgInput=document.querySelector("input[name='fg_color']");
    const bgInput=document.querySelector("input[name='bg_color']");
    const dataInput=document.querySelector("input[name='data']");
    const logoInput=document.querySelector("input[name='logo']");
    const form=document.querySelector("form");

    //zone d'apercu text/couleur
    const preview=document.createElement("div");
    preview.style.marginTop="15px";
    preview.style.padding="10px";
    preview.style.borderRadius="6px";
    preview.style.border="1px dashed #ccc";
    preview.innerText="preview colors here";
    form.appendChild(preview);

    //zone d'apercu logo
    const logoPreview=document.createElement("img");
    logoPreview.style.marginTop="15px";
    logoPreview.style.maxWidth="100px";
    logoPreview.style.display="none";
    form.appendChild(logoPreview);

    //mettre a jour l'apercu text/couleur
    function updatepreview(){
        preview.style.color=fgInput.Value;
        preview.style.backgroundColor=bgInput.Value;
        preview.innerText=dataInput.value || "QR preview Text";
    }

    fgInput.addEventListener("input",updatepreview);
    bgInput.addEventListener("input",updatepreview);
    dataInput.addEventListener("input",updatepreview);

    //apercu du logo uploade
    logoInput.addEventListener("change",()=>{
        const file=logoInput.files[0];
        if(file){
            const reader=new FileReader();
            reader.onload=(e)=>{
                logoPreview.src=e.target.result;
                logoPreview.style.display="block";
            };
            reader.readAsDataURL(file);
        }else{
            logoPreview.style.display="none";
        }
    });

    //verification avant envoi
    form.addEventListener("submit",(e)=>{
        if(!dataInput.value.trim()){
            e.preventDefault();
            alert("Veuillez enter dutexte ou une URL!");
        }
    });
});